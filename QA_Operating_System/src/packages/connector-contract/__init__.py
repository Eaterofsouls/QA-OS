"""
connector-contract package.

Exports the universal Connector Protocol interface along with all
shared data models used across every connector adapter.

Usage::

    from connector_contract import Connector, ConnectorEvent, ConnectorCredentials, StatusPost
"""

from .interface import (
    Connector,
    ConnectorEvent,
    ConnectorCredentials,
    StatusPost,
)

__all__ = [
    "Connector",
    "ConnectorEvent",
    "ConnectorCredentials",
    "StatusPost",
]
