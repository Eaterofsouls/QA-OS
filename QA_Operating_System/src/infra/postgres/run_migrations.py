"""
infra/postgres/run_migrations.py
=================================
Idempotent PostgreSQL migration runner for the AI QA Operating System.

Usage:
    DATABASE_URL=postgresql://user:pass@host:5432/db \\
        uv run python infra/postgres/run_migrations.py

    # Or with the .env file already populated:
    uv run python infra/postgres/run_migrations.py

Behaviour:
- Scans ``infra/postgres/migrations/`` for ``*.sql`` files (sorted lexicographically).
- On first run, applies ``0000_init.sql`` which creates the ``_migrations`` table.
- For every subsequent file:
    - Checks ``_migrations`` for an existing row with the same name.
    - If already applied → prints ``[SKIP]`` and moves on.
    - If not applied → runs the file inside a transaction, prints ``[RUN]``.
- Exits with code 0 on full success, code 1 on any error.

The runner uses ``psycopg2`` if available, falling back to ``subprocess psql``
if psycopg2 is not installed (useful in minimal CI environments).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env (no-op when running in a properly configured environment)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MIGRATIONS_DIR: Path = Path(__file__).parent / "migrations"
MIGRATION_FILE_PATTERN = re.compile(r"^\d{4}_.*\.sql$")


# ---------------------------------------------------------------------------
# Helper: resolve migration name from file path
# ---------------------------------------------------------------------------

def migration_name(path: Path) -> str:
    """
    Derive the canonical migration name from a ``.sql`` file path.

    Parameters
    ----------
    path:
        Absolute or relative path to the SQL file.

    Returns
    -------
    str
        The stem of the file name, e.g. ``"0001_cost_ledger"``.
    """
    return path.stem


# ---------------------------------------------------------------------------
# psycopg2-based implementation
# ---------------------------------------------------------------------------

def _run_with_psycopg2(database_url: str, migrations: list[Path]) -> None:
    """
    Apply pending migrations using the ``psycopg2`` driver.

    Parameters
    ----------
    database_url:
        Full PostgreSQL connection URL.
    migrations:
        Ordered list of ``.sql`` migration files to process.

    Raises
    ------
    SystemExit
        Exits with code 1 on any error.
    """
    try:
        import psycopg2  # type: ignore[import]
        from psycopg2.extras import DictCursor  # type: ignore[import]
    except ImportError:
        print(
            "[ERROR] psycopg2 is not installed and no psql fallback is available.\n"
            "        Install it with: uv add psycopg2-binary",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    conn.autocommit = False

    try:
        # Ensure the _migrations table exists (0000_init.sql does this,
        # but we need a minimal bootstrap in case the user runs the runner
        # before running 0000_init manually).
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS _migrations (
                    id         SERIAL PRIMARY KEY,
                    name       VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        conn.commit()

        for path in migrations:
            name = migration_name(path)

            # Check if already applied
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(
                    "SELECT applied_at FROM _migrations WHERE name = %s",
                    (name,),
                )
                row = cur.fetchone()

            if row:
                print(
                    f"[SKIP]  {name:<40} (already applied {row['applied_at'].strftime('%Y-%m-%d %H:%M:%S%z')})"
                )
                continue

            # Apply the migration
            sql_content = path.read_text(encoding="utf-8")
            print(f"[RUN ]  {name:<40} ...", end=" ", flush=True)

            try:
                with conn.cursor() as cur:
                    cur.execute(sql_content)
                conn.commit()
                print("OK")
            except Exception as exc:
                conn.rollback()
                print(f"FAILED\n[ERROR] {exc}", file=sys.stderr)
                sys.exit(1)

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# psql subprocess fallback
# ---------------------------------------------------------------------------

def _run_with_psql(database_url: str, migrations: list[Path]) -> None:
    """
    Apply migrations via the ``psql`` command-line tool (fallback).

    This implementation cannot check the ``_migrations`` table for already-
    applied migrations, so it relies on idempotent SQL (``CREATE TABLE IF NOT
    EXISTS``, ``INSERT ... ON CONFLICT DO NOTHING``).

    Parameters
    ----------
    database_url:
        Full PostgreSQL connection URL.
    migrations:
        Ordered list of ``.sql`` migration files to process.

    Raises
    ------
    SystemExit
        Exits with code 1 on any error.
    """
    print(
        "[WARN] psycopg2 not available — using psql subprocess fallback.\n"
        "       Install psycopg2-binary for idempotency checking.",
        file=sys.stderr,
    )

    psql_path = _find_psql()
    if not psql_path:
        print(
            "[ERROR] Neither psycopg2 nor psql found. Cannot run migrations.",
            file=sys.stderr,
        )
        sys.exit(1)

    for path in migrations:
        name = migration_name(path)
        print(f"[RUN ]  {name:<40} ...", end=" ", flush=True)
        result = subprocess.run(
            [psql_path, database_url, "-f", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"FAILED\n[ERROR] {result.stderr}", file=sys.stderr)
            sys.exit(1)
        print("OK")


def _find_psql() -> Optional[str]:
    """
    Locate the ``psql`` binary on the system PATH.

    Returns
    -------
    str or None
        Absolute path to ``psql``, or ``None`` if not found.
    """
    import shutil
    return shutil.which("psql")


# ---------------------------------------------------------------------------
# Runner entry point
# ---------------------------------------------------------------------------

def run(database_url: str, migrations_dir: Path = MIGRATIONS_DIR) -> None:
    """
    Discover and apply all pending migrations in *migrations_dir*.

    Parameters
    ----------
    database_url:
        Full PostgreSQL connection URL.
    migrations_dir:
        Directory containing ``.sql`` migration files.  Files must match
        ``NNNN_name.sql`` (four-digit prefix).

    Raises
    ------
    SystemExit
        Exits with code 1 if the migrations directory is missing or if any
        migration fails.
    """
    if not migrations_dir.is_dir():
        print(
            f"[ERROR] Migrations directory not found: {migrations_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Collect migration files matching NNNN_*.sql, sorted lexicographically
    migrations: list[Path] = sorted(
        p for p in migrations_dir.iterdir()
        if p.is_file() and MIGRATION_FILE_PATTERN.match(p.name)
    )

    if not migrations:
        print("[INFO] No migration files found — nothing to do.")
        return

    print(f"[INFO] Found {len(migrations)} migration file(s) in {migrations_dir}")

    # Try psycopg2 first; fall back to psql
    try:
        import psycopg2  # type: ignore[import]  # noqa: F401
        _run_with_psycopg2(database_url, migrations)
    except ImportError:
        _run_with_psql(database_url, migrations)

    print("\n[INFO] All migrations complete.")


def main() -> int:
    """
    CLI entry point.

    Reads ``DATABASE_URL`` from the environment and calls :func:`run`.

    Returns
    -------
    int
        ``0`` on success.  (Failures call ``sys.exit(1)`` internally.)
    """
    database_url: str | None = os.getenv("DATABASE_URL")
    if not database_url:
        print(
            "[ERROR] DATABASE_URL environment variable is not set.\n"
            "        Example: DATABASE_URL=postgresql://qa_os:pass@localhost:5432/qa_os",
            file=sys.stderr,
        )
        return 1

    run(database_url)
    return 0


# ---------------------------------------------------------------------------
# Script guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
