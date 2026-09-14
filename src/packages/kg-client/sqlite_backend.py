"""SQLite-backed implementation of KGClientInterface.

Same contract as interface.py, same *semantics* as KGClientStub (stub.py) --
in particular get_related()'s foreign-key-style property scan (there's no
real edge store here either; create_relationship() remains a documented
no-op, exactly as in the stub) and find_similar_requirements()'s TF-IDF
cosine similarity (see similarity.py) -- just backed by a local SQLite file
instead of a process-memory dict, so demo data survives a server restart.

This is NOT a real graph database and isn't trying to be one -- it's the
same Sprint-0-grade node store the stub already is, with persistence
bolted on. If/when a real graph store is wanted, that's client.py's job
(Neo4j), not this file's.

Path comes from the KG_SQLITE_PATH env var (default: "./kg_data.sqlite3",
relative to wherever the process is started) -- see README.md §5 for how
to point the API at it, and get_client() in client.py for how this gets
selected over the in-memory stub.

One deliberate, harmless divergence from KGClientStub worth calling out
explicitly rather than leaving silent: KGClientStub.upsert_node() mutates
the caller's `properties` dict in place (`properties["tenant_id"] = ...`)
before storing it, as a side effect of using the same dict object as both
the argument and the stored value. This class does not mutate the
caller's dict -- it copies before adding tenant_id -- because there's no
reason to reproduce an incidental aliasing side effect just to match it,
and no current caller (module-01/02/03, services/api/main.py) relies on
the passed-in dict being mutated after the call returns. Every
*observable* behavior (what's returned by get_node/get_related/
find_similar_requirements, what upsert_node returns, what's stored) is
otherwise identical.
"""
import json
import os
import sqlite3
import uuid
from uuid import UUID

from .interface import KGClientInterface
from .tenant_scope import TenantScopeEnforcer
from .similarity import DEFAULT_SIMILARITY_THRESHOLD, cosine_similarity, tfidf_vectors

DEFAULT_SQLITE_PATH = "./kg_data.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    tenant_id  TEXT NOT NULL,
    node_id    TEXT NOT NULL,
    label      TEXT NOT NULL,
    properties TEXT NOT NULL,
    PRIMARY KEY (tenant_id, node_id)
);
"""

# Mirrors KGClientStub.get_related()'s reference_fields tuple exactly --
# see that method's docstring in stub.py for the full rationale (module-02
# generator.py's TestCase.requirement_id, module-01 assessor.py's
# RiskAssessmentOutput.requirement_id, fixtures.py's FIXTURE_RELATIONSHIPS
# from_id/to_id shape).
_REFERENCE_FIELDS = ("requirement_id", "covers_requirement", "from_id", "to_id")


class KGClientSQLite(KGClientInterface):
    """Sprint-0-grade node store (same as KGClientStub), persisted to a
    local SQLite file instead of self.nodes. See module docstring above.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv("KG_SQLITE_PATH", DEFAULT_SQLITE_PATH)
        # check_same_thread=False: FastAPI's async routes and this stdlib
        # sqlite3 connection both run on the single asyncio event-loop
        # thread in this deployment (no worker-thread pool is used for
        # these calls), so there's no real cross-thread contention -- this
        # only relaxes sqlite3's default same-thread assertion, which is
        # stricter than this single-process, single-thread demo needs.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute(_SCHEMA)
        self._conn.commit()
        # Unused directly, same as KGClientStub and KGClient -- kept for
        # interface/shape parity with the other two implementations.
        self.enforcer = TenantScopeEnforcer()

    async def upsert_node(self, tenant_id: UUID, label: str, properties: dict) -> str:
        node_id = properties.get("id", str(uuid.uuid4()))
        stored_properties = dict(properties)
        stored_properties["tenant_id"] = str(tenant_id)
        self._conn.execute(
            "INSERT INTO nodes (tenant_id, node_id, label, properties) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (tenant_id, node_id) DO UPDATE SET "
            "label = excluded.label, properties = excluded.properties",
            (str(tenant_id), node_id, label, json.dumps(stored_properties, default=str)),
        )
        self._conn.commit()
        return node_id

    async def get_node(self, tenant_id: UUID, node_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT properties FROM nodes WHERE tenant_id = ? AND node_id = ?",
            (str(tenant_id), node_id),
        ).fetchone()
        return json.loads(row[0]) if row else None

    async def create_relationship(self, tenant_id: UUID, from_id: str, to_id: str, rel_type: str, properties: dict | None = None) -> str:
        # Same documented no-op as KGClientStub.create_relationship() above
        # -- no edge table here either. get_related() below uses the same
        # foreign-key-style property scan the stub does, not a real edge
        # store, for exactly the same reason (see stub.py's TODO).
        return f"rel-{uuid.uuid4()}"

    async def get_related(self, tenant_id: UUID, node_id: str, rel_type: str | None = None, direction: str = "BOTH") -> list[dict]:
        """Same traversal semantics as KGClientStub.get_related() -- see
        that method's docstring in stub.py for the full rationale. `direction`
        is accepted for interface compatibility, not applied -- same as the
        stub, for the same reason (no real directed edges to distinguish).
        """
        tenant_key = str(tenant_id)
        rows = self._conn.execute(
            "SELECT node_id, label, properties FROM nodes WHERE tenant_id = ?",
            (tenant_key,),
        ).fetchall()

        related: list[dict] = []
        for n_id, label, properties_json in rows:
            if n_id == node_id:
                continue
            props = json.loads(properties_json)
            references_node = any(props.get(field) == node_id for field in _REFERENCE_FIELDS)
            if not references_node:
                continue
            if rel_type is not None and props.get("rel_type") not in (rel_type, None):
                continue
            related.append({**props, "id": n_id, "label": label})
        return related

    async def find_similar_requirements(
        self,
        tenant_id: UUID,
        requirement_text: str,
        exclude_requirement_id: str | None = None,
        limit: int = 3,
        min_similarity: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> list[dict]:
        """Same TF-IDF cosine-similarity semantics as
        KGClientStub.find_similar_requirements() -- see that method's
        docstring in stub.py, including why 0.2 is the default threshold
        (similarity.py) -- just sourced from SQLite-persisted Requirement
        nodes instead of a process-memory dict.
        """
        tenant_key = str(tenant_id)
        rows = self._conn.execute(
            "SELECT node_id, properties FROM nodes WHERE tenant_id = ? AND label = ?",
            (tenant_key, "Requirement"),
        ).fetchall()

        candidates: list[tuple[str, str]] = []
        for n_id, properties_json in rows:
            if n_id == exclude_requirement_id:
                continue
            text = json.loads(properties_json).get("text")
            if text:
                candidates.append((n_id, text))

        if not candidates:
            return []

        documents = [requirement_text] + [text for _, text in candidates]
        vectors = tfidf_vectors(documents)
        query_vector = vectors[0]

        scored: list[dict] = []
        for (n_id, text), candidate_vector in zip(candidates, vectors[1:]):
            similarity = cosine_similarity(query_vector, candidate_vector)
            if similarity >= min_similarity:
                scored.append({"id": n_id, "text": text, "similarity": round(similarity, 4)})

        scored.sort(key=lambda match: match["similarity"], reverse=True)
        return scored[:limit]

    async def vector_search(self, tenant_id: UUID, embedding: list[float], label: str | None = None, limit: int = 10) -> list[dict]:
        # Same documented no-op as KGClientStub.vector_search() -- SQLite
        # has no native vector index either. Out of scope for this pass.
        return []

    async def hybrid_search(self, tenant_id: UUID, query: str, embedding: list[float], label: str | None = None, limit: int = 10) -> list[dict]:
        # Same documented no-op as KGClientStub.hybrid_search().
        return []

    async def delete_node(self, tenant_id: UUID, node_id: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM nodes WHERE tenant_id = ? AND node_id = ?",
            (str(tenant_id), node_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    async def health_check(self) -> bool:
        try:
            self._conn.execute("SELECT 1")
            return True
        except Exception:
            return False
