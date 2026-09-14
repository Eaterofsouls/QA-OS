"""
infra/neo4j/connectivity_check.py
==================================
Neo4j connectivity verification script for the AI QA Operating System.

Usage (script):
    python infra/neo4j/connectivity_check.py

Usage (importable):
    from infra.neo4j.connectivity_check import check_connectivity, ConnectivityResult

Environment variables:
    NEO4J_URI       - Bolt endpoint (default: bolt://localhost:7687)
    NEO4J_USER      - Username (default: neo4j)
    NEO4J_PASSWORD  - Password (required)
    NEO4J_DATABASE  - Database name (default: neo4j)
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, exceptions as neo4j_exceptions

# ---------------------------------------------------------------------------
# Load .env if present (no-op if running in a container with real env vars)
# ---------------------------------------------------------------------------
load_dotenv()


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ConnectivityResult:
    """
    Result of a Neo4j connectivity check.

    Attributes:
        success:         True when the check completed without errors.
        server_version:  Raw version string returned by the server.
        server_address:  Host:port as reported by the driver.
        database:        Database name that was verified.
        test_value:      Value returned by ``RETURN 1 as n`` (should be 1).
        error:           Exception message on failure, else empty string.
    """
    success: bool
    server_version: str = ""
    server_address: str = ""
    database: str = ""
    test_value: Optional[int] = None
    error: str = ""


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def build_driver(
    uri: str,
    user: str,
    password: str,
    max_connection_lifetime: int = 3600,
) -> Driver:
    """
    Construct and return a Neo4j :class:`~neo4j.Driver` instance.

    Parameters
    ----------
    uri:
        Bolt endpoint, e.g. ``bolt://localhost:7687``.
    user:
        Neo4j username.
    password:
        Neo4j password.
    max_connection_lifetime:
        Seconds before the driver closes idle connections (default 3600).

    Returns
    -------
    Driver
        A configured but not yet verified driver.
    """
    return GraphDatabase.driver(
        uri,
        auth=(user, password),
        max_connection_lifetime=max_connection_lifetime,
    )


def check_connectivity(
    uri: str,
    user: str,
    password: str,
    database: str = "neo4j",
) -> ConnectivityResult:
    """
    Attempt to connect to Neo4j, run a trivial query, and return the result.

    The function is intentionally side-effect free — it does not print
    anything and does not call ``sys.exit()``.  Use :func:`main` for the
    CLI behaviour.

    Parameters
    ----------
    uri:
        Bolt endpoint URL.
    user:
        Neo4j username.
    password:
        Neo4j password.
    database:
        Target database (default ``"neo4j"``).

    Returns
    -------
    ConnectivityResult
        A dataclass describing the outcome.
    """
    driver: Optional[Driver] = None
    try:
        driver = build_driver(uri, user, password)

        # Verify connectivity by calling the server info endpoint
        server_info = driver.get_server_info()
        server_version: str = getattr(server_info, "agent", "unknown")
        server_address: str = getattr(server_info, "address", uri)

        # Run the canonical smoke test
        with driver.session(database=database) as session:
            result = session.run("RETURN 1 AS n")
            record = result.single()
            test_value: int = record["n"] if record else -1

        return ConnectivityResult(
            success=True,
            server_version=str(server_version),
            server_address=str(server_address),
            database=database,
            test_value=test_value,
        )

    except neo4j_exceptions.AuthError as exc:
        return ConnectivityResult(
            success=False,
            error=f"Authentication failed: {exc}",
        )
    except neo4j_exceptions.ServiceUnavailable as exc:
        return ConnectivityResult(
            success=False,
            error=f"Service unavailable — is Neo4j running? Detail: {exc}",
        )
    except Exception as exc:  # noqa: BLE001
        return ConnectivityResult(
            success=False,
            error=f"Unexpected error: {type(exc).__name__}: {exc}",
        )
    finally:
        if driver is not None:
            driver.close()


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    """
    CLI entrypoint.  Reads configuration from environment variables, runs the
    connectivity check, prints a human-readable report, and returns an exit
    code.

    Returns
    -------
    int
        ``0`` on success, ``1`` on failure.
    """
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user: str = os.getenv("NEO4J_USER", "neo4j")
    password: str | None = os.getenv("NEO4J_PASSWORD")
    database: str = os.getenv("NEO4J_DATABASE", "neo4j")

    if not password:
        print(
            "[ERROR] NEO4J_PASSWORD environment variable is not set.\n"
            "        Set it in your .env file or export it before running.",
            file=sys.stderr,
        )
        return 1

    print(f"Connecting to Neo4j at {uri} (database: {database}) ...", flush=True)

    result: ConnectivityResult = check_connectivity(uri, user, password, database)

    if result.success:
        print(
            f"\n[OK]  Connected to Neo4j\n"
            f"      Server version : {result.server_version}\n"
            f"      Server address : {result.server_address}\n"
            f"      Database       : {result.database}\n"
            f"      Test query     : RETURN 1 → n={result.test_value}\n"
        )
        return 0
    else:
        print(
            f"\n[FAIL] Neo4j connectivity check failed.\n"
            f"       Reason: {result.error}\n",
            file=sys.stderr,
        )
        return 1


# ---------------------------------------------------------------------------
# Script guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
