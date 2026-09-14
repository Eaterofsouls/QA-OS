"""
jira.models.generated
=====================

Pydantic models for Jira Cloud REST API v3 responses.

# Generated from Jira OpenAPI spec via datamodel-code-generator. DO NOT HAND-EDIT.

These models represent the minimal surface of the Jira API used by the
adapter.  Additional fields from the API response are captured via
``model_config = {"extra": "allow"}`` so the raw payload is preserved.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class JiraUser(BaseModel):
    """
    Represents a Jira user (assignee, reporter, etc.).

    # Generated from Jira OpenAPI spec via datamodel-code-generator. DO NOT HAND-EDIT.
    """

    account_id: Optional[str] = Field(None, alias="accountId")
    display_name: Optional[str] = Field(None, alias="displayName")
    email_address: Optional[str] = Field(None, alias="emailAddress")
    active: Optional[bool] = None
    avatar_urls: Optional[dict] = Field(None, alias="avatarUrls")

    model_config = {"extra": "allow", "populate_by_name": True}


class JiraStatus(BaseModel):
    """
    Represents a Jira issue status (e.g. 'To Do', 'In Progress', 'Done').

    # Generated from Jira OpenAPI spec via datamodel-code-generator. DO NOT HAND-EDIT.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status_category: Optional[dict] = Field(None, alias="statusCategory")

    model_config = {"extra": "allow", "populate_by_name": True}


class JiraProject(BaseModel):
    """
    Represents a Jira project.

    # Generated from Jira OpenAPI spec via datamodel-code-generator. DO NOT HAND-EDIT.
    """

    id: Optional[str] = None
    key: Optional[str] = None
    name: Optional[str] = None
    project_type_key: Optional[str] = Field(None, alias="projectTypeKey")
    avatar_urls: Optional[dict] = Field(None, alias="avatarUrls")

    model_config = {"extra": "allow", "populate_by_name": True}


# ---------------------------------------------------------------------------
# Primary ticket model
# ---------------------------------------------------------------------------


class JiraTicket(BaseModel):
    """
    Represents a Jira issue (ticket / story / bug / task).

    Captures all fields used by the translation layer; extra API fields
    are preserved in ``model_config = {"extra": "allow"}``.

    # Generated from Jira OpenAPI spec via datamodel-code-generator. DO NOT HAND-EDIT.
    """

    id: Optional[str] = None
    key: Optional[str] = None
    self_url: Optional[str] = Field(None, alias="self")

    # Nested fields object
    summary: Optional[str] = None
    description: Optional[dict] = None
    status: Optional[JiraStatus] = None
    assignee: Optional[JiraUser] = None
    reporter: Optional[JiraUser] = None
    project: Optional[JiraProject] = None
    priority: Optional[dict] = None
    labels: Optional[list[str]] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    resolution_date: Optional[str] = Field(None, alias="resolutiondate")
    comment: Optional[dict] = None

    model_config = {"extra": "allow", "populate_by_name": True}

    @classmethod
    def from_search_issue(cls, raw: dict) -> "JiraTicket":
        """
        Construct a JiraTicket from a raw search result issue dict.

        The Jira search API nests most data under a ``fields`` key::

            {
                "id": "10001",
                "key": "PROJ-1",
                "self": "https://...",
                "fields": { "summary": "...", ... }
            }

        Parameters
        ----------
        raw:
            Raw dict from Jira ``/rest/api/3/search`` response.

        Returns
        -------
        JiraTicket
            Populated ticket model.
        """
        fields: dict = raw.get("fields", {})
        return cls(
            id=raw.get("id"),
            key=raw.get("key"),
            **{"self": raw.get("self")},
            summary=fields.get("summary"),
            description=fields.get("description"),
            status=JiraStatus(**fields["status"]) if fields.get("status") else None,
            assignee=JiraUser(**fields["assignee"]) if fields.get("assignee") else None,
            reporter=JiraUser(**fields["reporter"]) if fields.get("reporter") else None,
            project=JiraProject(**fields["project"]) if fields.get("project") else None,
            priority=fields.get("priority"),
            labels=fields.get("labels", []),
            created=fields.get("created"),
            updated=fields.get("updated"),
            comment=fields.get("comment"),
        )
