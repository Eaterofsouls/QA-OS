"""
test_contract.py
================

Generic contract test suite for the Connector Protocol.

These tests are **tool-agnostic** — they validate that any object claiming
to implement the Connector interface:

1. Exposes all four required async methods.
2. Returns the correct data types from each method.
3. Respects the ``StatusPost.advisory_only=True`` invariant.
4. Passes the ``isinstance(obj, Connector)`` runtime check.

Usage
-----
Import the ``run_connector_contract`` helper and point it at any adapter::

    from tests.test_contract import run_connector_contract
    from my_adapter import MyAdapter

    @pytest.mark.asyncio
    async def test_my_adapter():
        await run_connector_contract(MyAdapter())

All tests in this module run against the bundled ``FakeConnector`` by default.
"""

from __future__ import annotations

import datetime
import inspect

import pytest

from connector_contract import (
    Connector,
    ConnectorCredentials,
    ConnectorEvent,
    StatusPost,
)
from connector_contract.tests.fakes.fake_connector import FakeConnector


# ---------------------------------------------------------------------------
# Helper: reusable contract runner
# ---------------------------------------------------------------------------


async def run_connector_contract(adapter: object) -> None:
    """
    Run the full contract test suite against *any* Connector implementer.

    Parameters
    ----------
    adapter:
        An instance of any class claiming to implement the Connector protocol.

    Raises
    ------
    AssertionError
        If any contract invariant is violated.
    """
    # 1. Runtime-checkable isinstance
    assert isinstance(adapter, Connector), (
        f"{type(adapter).__name__} does not satisfy the Connector Protocol"
    )

    # 2. All four methods exist and are coroutine functions
    for method_name in ("authenticate", "subscribe", "fetch", "post_status_back"):
        method = getattr(adapter, method_name, None)
        assert method is not None, f"Missing method: {method_name}"
        assert inspect.iscoroutinefunction(method), (
            f"{method_name} must be an async coroutine function"
        )

    creds = ConnectorCredentials(
        tool="test-tool", credentials={"token": "fake-token"}
    )

    # 3. authenticate() returns bool
    result = await adapter.authenticate(creds)  # type: ignore[attr-defined]
    assert isinstance(result, bool), "authenticate() must return bool"

    # 4. subscribe() returns str
    sub_id = await adapter.subscribe("tenant-001", ["ticket", "pr"])  # type: ignore[attr-defined]
    assert isinstance(sub_id, str) and sub_id, "subscribe() must return non-empty str"

    # 5. fetch() returns list[ConnectorEvent]
    events = await adapter.fetch("tenant-001", since=None)  # type: ignore[attr-defined]
    assert isinstance(events, list), "fetch() must return a list"
    for evt in events:
        assert isinstance(evt, ConnectorEvent), (
            f"fetch() must yield ConnectorEvent, got {type(evt)}"
        )

    # 6. post_status_back() returns bool
    post = StatusPost(
        event_id="evt-001",
        status="advisory",
        message="Contract test advisory",
        advisory_only=True,
    )
    posted = await adapter.post_status_back(post)  # type: ignore[attr-defined]
    assert isinstance(posted, bool), "post_status_back() must return bool"


# ---------------------------------------------------------------------------
# Unit tests for data models
# ---------------------------------------------------------------------------


class TestStatusPostDefaults:
    """Tests that StatusPost enforces advisory_only=True by default."""

    def test_advisory_only_defaults_to_true(self) -> None:
        """``StatusPost.advisory_only`` must default to ``True``."""
        post = StatusPost(
            event_id="e-001",
            status="passed",
            message="All good",
        )
        assert post.advisory_only is True, (
            "advisory_only must default to True — connectors never block autonomously"
        )

    def test_advisory_only_can_be_set_true_explicitly(self) -> None:
        """Explicit ``True`` is always accepted."""
        post = StatusPost(
            event_id="e-002",
            status="failed",
            message="Something went wrong",
            advisory_only=True,
        )
        assert post.advisory_only is True

    def test_status_post_fields_present(self) -> None:
        """All required fields must be present."""
        post = StatusPost(
            event_id="e-003",
            status="in_progress",
            message="Running checks",
        )
        assert post.event_id == "e-003"
        assert post.status == "in_progress"
        assert post.message == "Running checks"


class TestConnectorEventModel:
    """Tests that ConnectorEvent holds required fields correctly."""

    def test_connector_event_fields(self) -> None:
        """ConnectorEvent must accept all required fields."""
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        evt = ConnectorEvent(
            id="evt-123",
            tool="jira",
            event_type="ticket",
            raw_payload={"key": "PROJ-1"},
            normalized_at=now,
            tenant_id="tenant-abc",
        )
        assert evt.id == "evt-123"
        assert evt.tool == "jira"
        assert evt.event_type == "ticket"
        assert evt.tenant_id == "tenant-abc"
        assert isinstance(evt.normalized_at, datetime.datetime)

    def test_connector_event_raw_payload_defaults_empty(self) -> None:
        """raw_payload should default to an empty dict."""
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        evt = ConnectorEvent(
            id="evt-124",
            tool="slack",
            event_type="message",
            normalized_at=now,
            tenant_id="tenant-xyz",
        )
        assert evt.raw_payload == {}


class TestConnectorCredentials:
    """Tests for ConnectorCredentials model."""

    def test_credentials_fields(self) -> None:
        """ConnectorCredentials must hold tool and credentials dict."""
        creds = ConnectorCredentials(
            tool="github",
            credentials={"token": "ghp_xxx"},
        )
        assert creds.tool == "github"
        assert creds.credentials["token"] == "ghp_xxx"

    def test_credentials_defaults_empty_dict(self) -> None:
        """credentials should default to an empty dict."""
        creds = ConnectorCredentials(tool="slack")
        assert creds.credentials == {}


# ---------------------------------------------------------------------------
# Contract tests against FakeConnector
# ---------------------------------------------------------------------------


class TestConnectorProtocolCompliance:
    """Runs the full contract suite against FakeConnector."""

    @pytest.mark.asyncio
    async def test_fake_connector_passes_contract(self) -> None:
        """FakeConnector must satisfy every contract invariant."""
        await run_connector_contract(FakeConnector())

    def test_fake_connector_isinstance_check(self) -> None:
        """FakeConnector must pass runtime isinstance check."""
        fake = FakeConnector()
        assert isinstance(fake, Connector), (
            "FakeConnector does not satisfy the Connector Protocol at runtime"
        )

    @pytest.mark.asyncio
    async def test_fetch_returns_at_least_one_event(self) -> None:
        """FakeConnector.fetch() must return at least one event for testing."""
        fake = FakeConnector()
        events = await fake.fetch("tenant-001")
        assert len(events) >= 1, "FakeConnector.fetch() must return at least one event"

    @pytest.mark.asyncio
    async def test_authenticate_returns_true(self) -> None:
        """FakeConnector.authenticate() must return True."""
        fake = FakeConnector()
        creds = ConnectorCredentials(
            tool="fake", credentials={"token": "fake-token"}
        )
        result = await fake.authenticate(creds)
        assert result is True

    @pytest.mark.asyncio
    async def test_subscribe_returns_non_empty_string(self) -> None:
        """FakeConnector.subscribe() must return a non-empty string."""
        fake = FakeConnector()
        sub_id = await fake.subscribe("tenant-001", ["ticket"])
        assert isinstance(sub_id, str) and sub_id

    @pytest.mark.asyncio
    async def test_post_status_back_returns_bool(self) -> None:
        """FakeConnector.post_status_back() must return bool."""
        fake = FakeConnector()
        post = StatusPost(
            event_id="evt-fake-001",
            status="advisory",
            message="Advisory note",
        )
        result = await fake.post_status_back(post)
        assert isinstance(result, bool)
