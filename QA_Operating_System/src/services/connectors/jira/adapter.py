"""
jira.adapter
============

Full Jira Cloud adapter implementing the universal ``Connector`` Protocol.

Configuration (via environment variables)
-----------------------------------------
``JIRA_BASE_URL``
    Base URL of the Jira Cloud instance, e.g.
    ``https://myorg.atlassian.net``.
``JIRA_EMAIL``
    Email address of the Jira account used for API authentication.
``JIRA_API_TOKEN``
    Jira API token generated at https://id.atlassian.com/manage-profile/security/api-tokens

Authentication scheme
---------------------
Jira Cloud uses HTTP Basic Auth where the username is the account email and
the password is an API token.  The adapter encodes this as a base-64
``Authorization: Basic ...`` header on every request.

Translation contract
--------------------
``fetch()`` translates raw Jira issue dicts into ``ConnectorEvent`` objects
using ``jira.translation.translate_ticket``.  No semantic interpretation is
performed here — that is the responsibility of downstream QA-OS modules.

Advisory-only contract
----------------------
``post_status_back()`` posts a comment to the Jira issue.  It never
transitions an issue, never rejects a PR, and never blocks a pipeline.
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from typing import Any

import httpx
from dotenv import load_dotenv

from connector_contract.interface import (
    Connector,
    ConnectorCredentials,
    ConnectorEvent,
    StatusPost,
)
from jira.translation import translate_ticket

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT = httpx.Timeout(30.0)
_DEFAULT_JQL = "updated >= -1d ORDER BY updated DESC"
_MAX_RESULTS = 50


class JiraAdapter:
    """
    Jira Cloud adapter implementing the :class:`Connector` Protocol.

    Reads ``JIRA_BASE_URL``, ``JIRA_EMAIL``, and ``JIRA_API_TOKEN`` from the
    environment.  Raises ``RuntimeError`` if any are missing when a method
    that requires them is called.

    All HTTP calls use ``httpx.AsyncClient`` with a 30-second timeout.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
        timeout: httpx.Timeout = _DEFAULT_TIMEOUT,
    ) -> None:
        """
        Initialise the Jira adapter.

        Parameters
        ----------
        base_url:
            Override for ``JIRA_BASE_URL`` env var.
        email:
            Override for ``JIRA_EMAIL`` env var.
        api_token:
            Override for ``JIRA_API_TOKEN`` env var.
        timeout:
            httpx timeout configuration.
        """
        self._base_url: str = (
            base_url or os.getenv("JIRA_BASE_URL", "")
        ).rstrip("/")
        self._email: str = email or os.getenv("JIRA_EMAIL", "")
        self._api_token: str = api_token or os.getenv("JIRA_API_TOKEN", "")
        self._timeout = timeout
        self._subscriptions: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _auth_header(self) -> str:
        """Build the Basic Auth header value."""
        raw = f"{self._email}:{self._api_token}"
        encoded = base64.b64encode(raw.encode()).decode()
        return f"Basic {encoded}"

    def _require_config(self) -> None:
        """Raise RuntimeError if required env vars are not set."""
        missing = [
            name
            for name, val in [
                ("JIRA_BASE_URL", self._base_url),
                ("JIRA_EMAIL", self._email),
                ("JIRA_API_TOKEN", self._api_token),
            ]
            if not val
        ]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    def _make_client(self) -> httpx.AsyncClient:
        """Create a configured httpx.AsyncClient."""
        return httpx.AsyncClient(
            headers={
                "Authorization": self._auth_header(),
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=self._timeout,
        )

    # ------------------------------------------------------------------
    # Connector Protocol methods
    # ------------------------------------------------------------------

    async def authenticate(self, credentials: ConnectorCredentials) -> bool:
        """
        Authenticate with Jira by calling the ``/rest/api/3/myself`` endpoint.

        Updates the adapter's internal credentials if the ``credentials``
        argument provides overrides.

        Parameters
        ----------
        credentials:
            Optional credential overrides.  If ``credentials.credentials``
            contains ``"api_token"`` and/or ``"email"``, they will be used
            in place of env vars.

        Returns
        -------
        bool
            ``True`` if the API returns HTTP 200, ``False`` otherwise.
        """
        # Allow credential injection for testing / multi-tenant scenarios
        if credentials.credentials.get("api_token"):
            self._api_token = credentials.credentials["api_token"]
        if credentials.credentials.get("email"):
            self._email = credentials.credentials["email"]
        if credentials.credentials.get("base_url"):
            self._base_url = credentials.credentials["base_url"].rstrip("/")

        self._require_config()

        url = f"{self._base_url}/rest/api/3/myself"
        try:
            async with self._make_client() as client:
                response = await client.get(url)
            if response.status_code == 200:
                logger.info("Jira authentication successful for %s", self._email)
                return True
            logger.warning(
                "Jira authentication failed: HTTP %s", response.status_code
            )
            return False
        except httpx.RequestError as exc:
            logger.error("Jira authentication request error: %s", exc)
            return False

    async def subscribe(self, tenant_id: str, event_types: list[str]) -> str:
        """
        Store a subscription configuration in memory.

        Jira does not have a native push subscription model for all event
        types, so this adapter stores the configuration locally and uses it
        during ``fetch()``.

        Parameters
        ----------
        tenant_id:
            Opaque tenant identifier.
        event_types:
            Event types to subscribe to (e.g. ``["ticket"]``).

        Returns
        -------
        str
            A UUID-based subscription ID.
        """
        sub_id = str(uuid.uuid4())
        self._subscriptions[sub_id] = {
            "tenant_id": tenant_id,
            "event_types": event_types,
        }
        logger.info(
            "Jira subscription created: id=%s tenant=%s types=%s",
            sub_id,
            tenant_id,
            event_types,
        )
        return sub_id

    async def fetch(
        self,
        tenant_id: str,
        since: None | __import__("datetime").datetime = None,
    ) -> list[ConnectorEvent]:
        """
        Fetch Jira issues using JQL and translate them to ``ConnectorEvent``s.

        Translation only — no semantic interpretation is performed.

        Parameters
        ----------
        tenant_id:
            Tenant identifier embedded in each returned event.
        since:
            Optional lower-bound timestamp.  If provided, JQL is restricted
            to issues updated on or after this time.

        Returns
        -------
        list[ConnectorEvent]
            Zero or more normalised ticket events.
        """
        import datetime as dt

        self._require_config()

        jql = _DEFAULT_JQL
        if since is not None:
            # Jira JQL uses a specific date format
            since_str = since.strftime("%Y-%m-%d %H:%M")
            jql = f'updated >= "{since_str}" ORDER BY updated DESC'

        url = f"{self._base_url}/rest/api/3/search"
        params = {
            "jql": jql,
            "maxResults": _MAX_RESULTS,
            "fields": "summary,status,assignee,reporter,project,priority,labels,created,updated,comment",
        }

        try:
            async with self._make_client() as client:
                response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.RequestError as exc:
            logger.error("Jira fetch request error: %s", exc)
            return []
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Jira fetch HTTP error: %s %s", exc.response.status_code, exc
            )
            return []

        data = response.json()
        issues: list[dict] = data.get("issues", [])

        events: list[ConnectorEvent] = []
        for raw_issue in issues:
            try:
                event = translate_ticket(raw_issue, tenant_id)
                events.append(event)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to translate Jira issue %s: %s",
                    raw_issue.get("key", "UNKNOWN"),
                    exc,
                )

        logger.info(
            "Fetched %d Jira events for tenant %s", len(events), tenant_id
        )
        return events

    async def post_status_back(self, post: StatusPost) -> bool:
        """
        Post an advisory comment to the Jira issue identified by
        ``post.event_id``.

        Advisory only — this method NEVER transitions an issue status,
        never rejects a PR, and never blocks a pipeline.

        Parameters
        ----------
        post:
            Status update.  ``event_id`` should be a Jira issue key
            (e.g. ``"PROJ-1"``).

        Returns
        -------
        bool
            ``True`` if the comment was posted successfully.
        """
        self._require_config()

        if not post.advisory_only:
            logger.error(
                "post_status_back called with advisory_only=False — rejected. "
                "Jira adapter never blocks autonomously."
            )
            raise ValueError(
                "advisory_only must be True — Jira adapter never blocks autonomously"
            )

        url = (
            f"{self._base_url}/rest/api/3/issue/{post.event_id}/comment"
        )
        body = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"[QA-OS Advisory — {post.status.upper()}] "
                                    f"{post.message}"
                                ),
                            }
                        ],
                    }
                ],
            }
        }

        try:
            async with self._make_client() as client:
                response = await client.post(url, json=body)
            if response.status_code in (200, 201):
                logger.info(
                    "Jira advisory comment posted on issue %s", post.event_id
                )
                return True
            logger.warning(
                "Jira comment post failed: HTTP %s for issue %s",
                response.status_code,
                post.event_id,
            )
            return False
        except httpx.RequestError as exc:
            logger.error("Jira post_status_back request error: %s", exc)
            return False
