"""
jira.translation
================

Translation only. Never interprets content.

This module transforms raw Jira API responses into normalised
``ConnectorEvent`` objects.  It performs **shape transformation only**:
field mapping, type coercion, and structural flattening.

It does NOT:

* Classify the semantic meaning of a ticket.
* Decide whether a ticket requires action.
* Trigger any downstream behaviour.

All interpretation is the responsibility of downstream QA-OS modules.
"""

from __future__ import annotations

import datetime
import logging

from connector_contract.interface import ConnectorEvent
from jira.models.generated import JiraTicket

logger = logging.getLogger(__name__)


def translate_ticket(raw: dict, tenant_id: str) -> ConnectorEvent:
    """
    Translate a raw Jira issue dict into a normalised ``ConnectorEvent``.

    Translation only. Never interprets content.

    The raw Jira search result is expected in the form returned by
    ``GET /rest/api/3/search``::

        {
            "id": "10001",
            "key": "PROJ-1",
            "self": "https://myorg.atlassian.net/rest/api/3/issue/10001",
            "fields": {
                "summary": "Fix the thing",
                "status": {"name": "In Progress", ...},
                "assignee": {"accountId": "...", "displayName": "Alice"},
                "created": "2024-01-01T00:00:00.000+0000",
                "updated": "2024-01-02T00:00:00.000+0000",
            }
        }

    Parameters
    ----------
    raw:
        Verbatim Jira issue dict from the search API.
    tenant_id:
        Opaque tenant identifier to embed in the event.

    Returns
    -------
    ConnectorEvent
        A normalised event with ``event_type="ticket"`` and the full
        raw payload preserved in ``raw_payload``.

    Notes
    -----
    Translation only. Never interprets content.
    """
    ticket = JiraTicket.from_search_issue(raw)

    fields: dict = raw.get("fields", {})

    # Extract assignee display name safely
    assignee_name: str | None = None
    if ticket.assignee:
        assignee_name = ticket.assignee.display_name

    # Extract status name safely
    status_name: str | None = None
    if ticket.status:
        status_name = ticket.status.name

    # Build normalised payload — shape only, no interpretation
    normalised_payload: dict = {
        "id": ticket.id,
        "key": ticket.key,
        "summary": ticket.summary,
        "status": status_name,
        "assignee": assignee_name,
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        # Preserve full raw fields for downstream use
        "_raw": raw,
    }

    logger.debug(
        "Translated Jira ticket %s for tenant %s",
        ticket.key,
        tenant_id,
    )

    return ConnectorEvent(
        id=str(ticket.key or ticket.id or "unknown"),
        tool="jira",
        event_type="ticket",
        raw_payload=normalised_payload,
        normalized_at=datetime.datetime.now(tz=datetime.timezone.utc),
        tenant_id=tenant_id,
    )
