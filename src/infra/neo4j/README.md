# Neo4j 5.26.x Enterprise LTS — Infrastructure Guide

> **Important:** This deployment uses the **Enterprise LTS** release line (`5.x`), **NOT** the CalVer release line. The Enterprise LTS line receives long-term support patches and is the only supported variant for production use in this system.

---

## Version Pins

| Component | Version |
|-----------|---------|
| Neo4j Server | `5.26.x` Enterprise LTS |
| Python Driver | `neo4j==5.28.1` |
| Bolt Protocol | `5.x` |

**Do NOT** upgrade to CalVer releases (e.g., `2025.x`, `2026.x`) without an explicit architecture decision record (ADR).

---

## Connection Details

### Environment Variables

```bash
NEO4J_URI=bolt://localhost:7687        # Bolt endpoint (default)
NEO4J_USER=neo4j
NEO4J_PASSWORD=<set-in-.env>
NEO4J_DATABASE=neo4j                   # default database
```

> For clustered/HA deployments, use `neo4j+s://` or `bolt+routing://` schemes.

### Bolt Endpoint

```
bolt://localhost:7687
```

The HTTP browser console (read-only, dev use only) is available at:

```
http://localhost:7474
```

---

## Driver Installation

Pin the exact driver version in all Python packages:

```toml
# pyproject.toml
[project.dependencies]
neo4j = "==5.28.1"
```

```bash
pip install "neo4j==5.28.1"
# or with uv:
uv add "neo4j==5.28.1"
```

---

## Docker Compose (Local Dev)

```yaml
services:
  neo4j:
    image: neo4j:5.26-enterprise
    environment:
      NEO4J_AUTH: "neo4j/${NEO4J_PASSWORD}"
      NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"
      NEO4J_dbms_memory_heap_max__size: "2G"
      NEO4J_dbms_memory_pagecache_size: "1G"
    ports:
      - "7474:7474"   # HTTP browser
      - "7687:7687"   # Bolt
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 5
volumes:
  neo4j_data:
  neo4j_logs:
```

---

## Connectivity Check

Run the bundled connectivity script to verify the connection:

```bash
uv run python infra/neo4j/connectivity_check.py
```

Expected output:

```
[OK] Connected to Neo4j
     Server version : Neo4j/5.26.0
     Server address : localhost:7687
     Database       : neo4j
     Test query     : RETURN 1 → n=1
```

---

## Schema & Indexes

The Graphiti memory layer manages its own schema. However, core indexes should be applied at bootstrap:

```cypher
-- Applied by Graphiti or infra bootstrap
CREATE CONSTRAINT entity_uuid IF NOT EXISTS
  FOR (e:Entity) REQUIRE e.uuid IS UNIQUE;

CREATE INDEX entity_name IF NOT EXISTS
  FOR (e:Entity) ON (e.name);
```

---

## Access Control (Enterprise LTS Feature)

Use Neo4j's native RBAC for multi-tenant isolation:

```cypher
CREATE ROLE qa_os_reader;
CREATE ROLE qa_os_writer;

GRANT TRAVERSE ON GRAPH * ELEMENTS * TO qa_os_reader;
GRANT READ {*} ON GRAPH * ELEMENTS * TO qa_os_reader;
GRANT WRITE ON GRAPH * ELEMENTS * TO qa_os_writer;
```

---

## Backup & DR

See [`infra/deploy/backup-dr-policy.md`](../deploy/backup-dr-policy.md) for the full Neo4j backup schedule, RTO, and RPO targets.

---

## References

- [Neo4j 5.x Enterprise Docs](https://neo4j.com/docs/operations-manual/5/)
- [Python Driver 5.28.x Docs](https://neo4j.com/docs/python-manual/current/)
- [Bolt Protocol Specification](https://neo4j.com/docs/bolt/current/)
