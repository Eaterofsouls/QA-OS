# kg-client

## STATUS: STUB-QUALITY (Sprint 0)

This package is currently using an in-memory stub implementation.
The real Neo4j-backed implementation is in `client.py` and activates automatically
when the `NEO4J_URI` environment variable is set.

---

## Stub-and-swap point

**Sprint 2 (Epic M7S.2)** swaps stub → real client.  
**Zero consumer code changes required.** The `get_client()` factory handles selection.

```python
# Consumer code — unchanged across Sprint 0 → Sprint 2:
from kg_client import get_client

client = get_client()          # returns stub (Sprint 0) or real client (Sprint 2)
node_id = await client.upsert_node(tenant_id, "Requirement", {"id": "req-1", ...})
```

---

## ADR-011: No Cypher outside this package

This is the **ONLY** code path permitted to issue Cypher queries.

- All other packages must import `get_client()` from `kg_client`.
- Direct use of the `neo4j` driver anywhere else is a lint violation
  (enforced by `.lint/rules/no-raw-cypher.py`).
- Every query passes through `TenantScopeEnforcer` — no bypass path exists.

---

## Environment Variables

| Variable        | Required     | Default   | Description                    |
|-----------------|-------------|-----------|--------------------------------|
| `NEO4J_URI`     | Sprint 2+   | (unset)   | Bolt URI, e.g. `bolt://...`   |
| `NEO4J_USER`    | Sprint 2+   | `neo4j`   | Neo4j username                 |
| `NEO4J_PASSWORD`| Sprint 2+   | (unset)   | Neo4j password                 |

---

## Package Structure

```
packages/kg-client/
├── __init__.py          # Public API: get_client(), KGClient, KGClientStub
├── interface.py         # Frozen Protocol — method signatures locked from Sprint 0
├── stub.py              # In-memory stub (Sprint 0)
├── client.py            # Real Neo4j client (Sprint 2, activates via env)
├── fixtures.py          # Sample data for stub/tests
├── tenant_scope.py      # TenantScopeEnforcer — ADR-011 chokepoint
└── tests/
    ├── test_stub.py             # Smoke tests for all 8 interface methods
    └── test_tenant_isolation.py # CRITICAL: proves data never leaks across tenants
```

---

## Tenant Isolation Contract

Tenant isolation is guaranteed at two levels:

1. **Stub**: `_store[tenant_id_str]` dict-key isolation — no cross-key access possible.
2. **Real client**: Every Cypher query has `WHERE n.tenant_id = $tenant_id` injected
   by `TenantScopeEnforcer` before execution.

The tests in `tests/test_tenant_isolation.py` are the **acceptance proof** — they
must pass for every commit that touches this package.
