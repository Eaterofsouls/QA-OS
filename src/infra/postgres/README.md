# PostgreSQL 16.x — Infrastructure Guide

> **Version:** PostgreSQL 16.x (pinned in Docker image `postgres:16-alpine`)  
> **Migration tooling:** Raw SQL files run by `infra/postgres/run_migrations.py`

---

## Connection Details

### Environment Variables

```bash
DATABASE_URL=postgresql://qa_os:password@localhost:5432/qa_os
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=qa_os
POSTGRES_USER=qa_os
POSTGRES_PASSWORD=<set-in-.env>
```

### Connection String Format

```
postgresql://<user>:<password>@<host>:<port>/<database>
```

Example (local dev):

```
postgresql://qa_os:devpassword@localhost:5432/qa_os
```

---

## Docker Compose (Local Dev)

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: qa_os
      POSTGRES_USER: qa_os
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U qa_os"]
      interval: 10s
      timeout: 5s
      retries: 5
volumes:
  postgres_data:
```

---

## Python Driver Installation

```toml
# pyproject.toml
[project.dependencies]
psycopg2-binary = ">=2.9,<3"
# or async:
asyncpg = ">=0.29,<1"
```

```bash
uv add "psycopg2-binary>=2.9,<3"
```

---

## Migration Tooling

This project uses **raw SQL migration files** — no ORM migration framework.  
Migrations are stored in `infra/postgres/migrations/` and named with a zero-padded numeric prefix:

```
migrations/
  0000_init.sql          ← creates _migrations tracking table
  0001_cost_ledger.sql   ← cost tracking schema
  0002_...sql
```

### Running Migrations

```bash
# Via the Python runner (recommended):
DATABASE_URL=postgresql://... uv run python infra/postgres/run_migrations.py

# Or directly in psql:
psql "$DATABASE_URL" -f infra/postgres/migrations/0000_init.sql
psql "$DATABASE_URL" -f infra/postgres/migrations/0001_cost_ledger.sql
```

### Migration Runner Behaviour

- Reads `DATABASE_URL` from environment (or `.env` file).
- Scans `infra/postgres/migrations/` for `*.sql` files sorted lexicographically.
- Before running each file, checks the `_migrations` table to see if it has already been applied.
- If already applied, **skips** it (idempotent).
- Wraps each migration in a transaction; on error the transaction is rolled back and the runner exits with code 1.
- Prints each migration name and status.

```
[SKIP]  0000_init         (already applied 2025-01-15 09:32:11+00)
[RUN ]  0001_cost_ledger  ... OK
```

---

## Schema Overview

| Table | Purpose |
|-------|---------|
| `_migrations` | Migration tracking (applied by `0000_init.sql`) |
| `cost_ledger` | Per-call LLM cost tracking (applied by `0001_cost_ledger.sql`) |

---

## Backup & DR

See [`infra/deploy/backup-dr-policy.md`](../deploy/backup-dr-policy.md).

PostgreSQL backups are taken via `pg_dump` on the schedule defined in the DR policy. Continuous WAL archiving is enabled in production.

---

## References

- [PostgreSQL 16 Release Notes](https://www.postgresql.org/docs/16/release-16.html)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [pg_dump Reference](https://www.postgresql.org/docs/16/app-pgdump.html)
