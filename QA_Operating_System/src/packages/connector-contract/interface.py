"""
connector_contract.interface
============================

Defines the universal Connector Protocol that every adapter (Jira, GitHub,
Slack, Playwright, Legacy, …) must implement.

Design principles
-----------------
* **Translation only** – connectors translate raw tool payloads into
  ``ConnectorEvent`` objects.  They NEVER interpret meaning or trigger
  autonomous actions.
* **Advisory only** – ``post_status_back`` always sends advisory messages;
  it NEVER blocks a pipeline autonomously (``StatusPost.advisory_only``
  defaults to ``True`` and must never be overridden to ``False`` inside
  a connector).
* **Protocol / runtime-checkable** – any class that duck-types all four
  methods satisfies the contract without explicit inheritance.
"""

from __future__ import annotations

import datetime
from typing import AsyncIterator, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ConnectorCredentials(BaseModel):
    """
    Holds authentication material for a specific tool.

    Attributes
    ----------
    tool:
        Canonical tool identifier, e.g. ``"jira"``, ``"github"``,
        ``"slack"``, ``"playwright"``.
    credentials:
        Free-form key/value pairs (e.g. ``{"api_token": "..."}``).
        Values should be treated as secrets and never logged.
    """

    tool: str = Field(..., description="Canonical tool identifier, e.g. 'jira'")
    credentials: dict[str, str] = Field(
        default_factory=dict,
        description="Secret key/value pairs — never log these.",
    )

    model_config = {"frozen": True}


class ConnectorEvent(BaseModel):
    """
    A normalised event emitted by a connector.

    This is the single data shape that flows out of every adapter into the
    rest of the QA-OS pipeline.  The connector performs *shape*
    transformation only; semantic interpretation belongs to downstream
    modules.

    Attributes
    ----------
    id:
        Unique event identifier (usually the tool's native ticket/PR/run ID).
    tool:
        Source tool identifier, e.g. ``"jira"``, ``"github"``.
    event_type:
        Coarse event classification.  Allowed values:
        ``"ticket"`` | ``"pr"`` | ``"message"`` | ``"test_result"``.
    raw_payload:
        The verbatim payload returned by the tool's API.  Downstream
        modules may inspect this for additional context.
    normalized_at:
        UTC timestamp when this event was created by the connector.
    tenant_id:
        Opaque tenant / workspace identifier used for multi-tenancy routing.
    """

    id: str = Field(..., description="Unique event ID from the source tool.")
    tool: str = Field(..., description="Source tool, e.g. 'jira'.")
    event_type: str = Field(
        ...,
        description="One of: 'ticket', 'pr', 'message', 'test_result'.",
    )
    raw_payload: dict = Field(
        default_factory=dict,
        description="Verbatim payload from the tool API — no interpretation.",
    )
    normalized_at: datetime.datetime = Field(
        ...,
        description="UTC timestamp of normalization.",
    )
    tenant_id: str = Field(..., description="Tenant / workspace identifier.")

    model_config = {"frozen": True}


class StatusPost(BaseModel):
    """
    A status update to be posted back to the originating tool.

    Critical safety note
    --------------------
    ``advisory_only`` MUST remain ``True``.  The QA-OS system is designed
    so that connectors NEVER autonomously block or fail a pipeline.
    Only a human can escalate a status from advisory to blocking.

    Attributes
    ----------
    event_id:
        The ``ConnectorEvent.id`` this status relates to.
    status:
        One of: ``"pending"`` | ``"in_progress"`` | ``"passed"`` |
        ``"failed"`` | ``"advisory"``.
    message:
        Human-readable status description.
    advisory_only:
        Always ``True``.  Never override to ``False`` inside a connector.
    """

    event_id: str = Field(..., description="ID of the ConnectorEvent being updated.")
    status: str = Field(
        ...,
        description=(
            "One of: 'pending', 'in_progress', 'passed', 'failed', 'advisory'."
        ),
    )
    message: str = Field(..., description="Human-readable status description.")
    advisory_only: bool = Field(
        default=True,
        description=(
            "Always True — connectors NEVER block autonomously. "
            "Only humans may escalate."
        ),
    )

    model_config = {"frozen": True}


@runtime_checkable
class Connector(Protocol):
    """
    Universal connector interface — all adapters must implement these four
    methods.

    Any class that provides all four async methods with compatible signatures
    satisfies this Protocol without needing to inherit from it explicitly.
    Use ``isinstance(obj, Connector)`` to check compliance at runtime thanks
    to ``@runtime_checkable``.

    Safety contract
    ---------------
    * ``fetch`` → translation only, never interpretation.
    * ``post_status_back`` → always advisory; ``StatusPost.advisory_only``
      must be ``True``.
    """

    async def authenticate(self, credentials: ConnectorCredentials) -> bool:
        """
        Authenticate with the external tool.

        Parameters
        ----------
        credentials:
            Tool credentials (token, API key, etc.).

        Returns
        -------
        bool
            ``True`` on successful authentication, ``False`` otherwise.
        """
        ...

    async def subscribe(self, tenant_id: str, event_types: list[str]) -> str:
        """
        Subscribe to events from the tool.

        Parameters
        ----------
        tenant_id:
            Tenant identifier for routing.
        event_types:
            List of event type strings to subscribe to, e.g.
            ``["ticket", "pr"]``.

        Returns
        -------
        str
            An opaque subscription ID that can be used to cancel or
            query the subscription.
        """
        ...

    async def fetch(
        self,
        tenant_id: str,
        since: datetime.datetime | None = None,
    ) -> list[ConnectorEvent]:
        """
        Fetch events from the tool.

        Translation only — never interpretation.  The connector maps raw
        API responses to ``ConnectorEvent`` objects without analysing their
        meaning.

        Parameters
        ----------
        tenant_id:
            Tenant identifier for routing.
        since:
            Optional lower-bound timestamp.  If ``None``, the adapter
            decides a sensible default (e.g. last 24 hours).

        Returns
        -------
        list[ConnectorEvent]
            Zero or more normalised events.
        """
        ...

    async def post_status_back(self, post: StatusPost) -> bool:
        """
        Post a status update back to the tool.

        Always advisory — never blocking.  The adapter must never set
        a conclusion that autonomously fails or blocks a pipeline.

        Parameters
        ----------
        post:
            Status update payload.  ``post.advisory_only`` must be ``True``.

        Returns
        -------
        bool
            ``True`` if the post was accepted by the tool.
        """
        ...
