"""
fake_connector.py
=================

Minimal compliance fake implementing the Connector Protocol.

Design
------
* **Zero real tool dependencies** — no Jira, GitHub, Slack, or any external
  SDK is imported.
* Returns fully-formed fixture data from all four methods.
* Intended for use in contract tests and as a reference implementation for
  new adapter authors.
* Passes the generic ``run_connector_contract`` test suite without
  modification.

Usage::

    from connector_contract.tests.fakes.fake_connector import FakeConnector

    fake = FakeConnector()
    events = await fake.fetch("tenant-001")
"""

from __future__ import annotations

import datetime
import uuid

from connector_contract.interface import (
    Connector,
    ConnectorCredentials,
    ConnectorEvent,
    StatusPost,
)

# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

_FIXTURE_EVENT = {
    "id": "FAKE-001",
    "summary": "Fake ticket for contract testing",
    "status": "open",
    "assignee": "test-user",
    "created": "2024-01-01T00:00:00Z",
    "updated": "2024-01-02T00:00:00Z",
}


class FakeConnector:
    """
    Minimal compliance fake implementing the :class:`Connector` Protocol.

    All methods return deterministic fixture data. There are zero network
    calls, zero external dependencies, and zero side effects.

    This class exists solely to:

    1. Prove the contract is implementable.
    2. Serve as a reference for new adapter authors.
    3. Enable the generic test suite to run without real infrastructure.
    """

    def __init__(self, *, tenant_prefix: str = "fake") -> None:
        """
        Initialise the fake connector.

        Parameters
        ----------
        tenant_prefix:
            Optional prefix applied to generated subscription IDs.
            Used only in tests that need unique IDs across multiple fakes.
        """
        self._tenant_prefix = tenant_prefix
        self._subscriptions: dict[str, dict] = {}
        self._authenticated: bool = False

    async def authenticate(self, credentials: ConnectorCredentials) -> bool:
        """
        Simulate successful authentication.

        Always returns ``True`` regardless of credentials content.
        No network calls are made.

        Parameters
        ----------
        credentials:
            Credentials object (ignored in this fake).

        Returns
        -------
        bool
            Always ``True``.
        """
        self._authenticated = True
        return True

    async def subscribe(self, tenant_id: str, event_types: list[str]) -> str:
        """
        Register a fake subscription and return a UUID-based subscription ID.

        Parameters
        ----------
        tenant_id:
            Opaque tenant identifier.
        event_types:
            List of event type strings (stored but not acted on).

        Returns
        -------
        str
            A unique subscription ID.
        """
        sub_id = f"{self._tenant_prefix}-{uuid.uuid4()}"
        self._subscriptions[sub_id] = {
            "tenant_id": tenant_id,
            "event_types": event_types,
        }
        return sub_id

    async def fetch(
        self,
        tenant_id: str,
        since: datetime.datetime | None = None,
    ) -> list[ConnectorEvent]:
        """
        Return a single hard-coded fixture ``ConnectorEvent``.

        Translation only — no interpretation of the payload.

        Parameters
        ----------
        tenant_id:
            Opaque tenant identifier used as ``ConnectorEvent.tenant_id``.
        since:
            Optional lower-bound timestamp (ignored in this fake).

        Returns
        -------
        list[ConnectorEvent]
            A list containing exactly one fixture event.
        """
        event = ConnectorEvent(
            id=_FIXTURE_EVENT["id"],
            tool="fake",
            event_type="ticket",
            raw_payload=dict(_FIXTURE_EVENT),
            normalized_at=datetime.datetime.now(tz=datetime.timezone.utc),
            tenant_id=tenant_id,
        )
        return [event]

    async def post_status_back(self, post: StatusPost) -> bool:
        """
        Simulate posting a status update back to the tool.

        No network calls are made; the post is merely recorded in memory.

        Parameters
        ----------
        post:
            Status update.  ``post.advisory_only`` must be ``True``.

        Returns
        -------
        bool
            Always ``True``.

        Raises
        ------
        ValueError
            If ``post.advisory_only`` is ``False`` — this fake enforces the
            advisory-only invariant strictly.
        """
        if not post.advisory_only:
            raise ValueError(
                "advisory_only must be True — connectors never block autonomously"
            )
        return True
