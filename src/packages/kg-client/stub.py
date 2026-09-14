from uuid import UUID
import uuid
from .interface import KGClientInterface
from .tenant_scope import TenantScopeEnforcer
from .similarity import DEFAULT_SIMILARITY_THRESHOLD, cosine_similarity, tfidf_vectors

class KGClientStub(KGClientInterface):
    """Sprint 0 in-memory stub."""
    def __init__(self):
        self.nodes = {}
        self.enforcer = TenantScopeEnforcer()
        
    async def upsert_node(self, tenant_id: UUID, label: str, properties: dict) -> str:
        node_id = properties.get("id", str(uuid.uuid4()))
        properties["tenant_id"] = str(tenant_id)
        self.nodes[(str(tenant_id), node_id)] = {"label": label, "properties": properties}
        return node_id

    async def get_node(self, tenant_id: UUID, node_id: str) -> dict | None:
        node = self.nodes.get((str(tenant_id), node_id))
        return node["properties"] if node else None

    async def create_relationship(self, tenant_id: UUID, from_id: str, to_id: str, rel_type: str, properties: dict | None = None) -> str:
        # TODO(kg-client, Sprint 2 swap-in): this stub does NOT persist the edge
        # anywhere -- self.nodes only stores nodes, there is no edge store. That
        # means a relationship created here is invisible to get_related() below.
        # Real edge storage + Cypher-backed traversal is explicitly out of scope
        # for the current "qualifying prototype" pass (see gap report A.3). The
        # returned id is not looked up anywhere; treat this as "call succeeded",
        # nothing more.
        return f"rel-{uuid.uuid4()}"

    async def get_related(self, tenant_id: UUID, node_id: str, rel_type: str | None = None, direction: str = "BOTH") -> list[dict]:
        """Sprint-0 traversal substitute.

        create_relationship() above is a documented no-op, so there is no real
        edge list to walk. Instead, this treats any *other* node in the same
        tenant whose properties carry a foreign-key-style reference to
        `node_id` as "related" -- this matches how callers actually link data
        today:
          - module-02 generator.py sets TestCase properties["requirement_id"]
            to the requirement being tested.
          - module-01 assessor.py's RiskAssessmentOutput.requirement_id
            round-trips the same requirement id.
          - fixtures.py's FIXTURE_RELATIONSHIPS shape (from_id/to_id/rel_type)
            is also honored, if that fixture data is ever loaded into
            self.nodes, since it uses the same field names.

        `direction` is accepted for interface compatibility but intentionally
        not applied -- without real directed edges there is no in/out to
        distinguish (TODO: revisit once Sprint 2 lands a real edge store).
        """
        tenant_key = str(tenant_id)
        reference_fields = ("requirement_id", "covers_requirement", "from_id", "to_id")
        related: list[dict] = []
        for (t_id, n_id), node in self.nodes.items():
            if t_id != tenant_key or n_id == node_id:
                continue
            props = node["properties"]
            references_node = any(props.get(field) == node_id for field in reference_fields)
            if not references_node:
                continue
            if rel_type is not None and props.get("rel_type") not in (rel_type, None):
                continue
            related.append({**props, "id": n_id, "label": node["label"]})
        return related

    async def find_similar_requirements(
        self,
        tenant_id: UUID,
        requirement_text: str,
        exclude_requirement_id: str | None = None,
        limit: int = 3,
        min_similarity: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> list[dict]:
        """Retrieval-based memory: TF-IDF cosine similarity over previously
        stored Requirement node text, scoped to this tenant (never crosses
        tenant boundaries -- same isolation as get_related() above).

        NOT a vector-embedding search and NOT model fine-tuning/training --
        see similarity.py's module docstring. This only ever looks at text
        already persisted via upsert_node("Requirement", ...); nothing here
        calls an LLM or any external service.

        Returns up to `limit` matches as
        `{"id": ..., "text": ..., "similarity": float}`, sorted by
        similarity descending, restricted to matches scoring at or above
        `min_similarity` (default: similarity.DEFAULT_SIMILARITY_THRESHOLD,
        see that module for why 0.2 was chosen). Returns an empty list --
        never a fabricated match -- when nothing in this tenant's stored
        Requirement nodes clears the threshold, including when this is the
        very first requirement for the tenant.
        """
        tenant_key = str(tenant_id)
        candidates: list[tuple[str, str]] = []
        for (t_id, n_id), node in self.nodes.items():
            if t_id != tenant_key or node["label"] != "Requirement" or n_id == exclude_requirement_id:
                continue
            text = node["properties"].get("text")
            if text:
                candidates.append((n_id, text))

        if not candidates:
            return []

        # documents[0] is the query; the rest are the stored candidates, in
        # the same order as `candidates` -- see tfidf_vectors()'s docstring
        # for why the query is included in the IDF calculation.
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
        # TODO(kg-client, Sprint 2 swap-in): needs a real vector index (Neo4j
        # GDS / native vector index). Out of scope for this pass -- documented
        # no-op, not silently pretending to search.
        return []

    async def hybrid_search(self, tenant_id: UUID, query: str, embedding: list[float], label: str | None = None, limit: int = 10) -> list[dict]:
        # TODO(kg-client, Sprint 2 swap-in): needs real text+vector hybrid
        # search against Neo4j. Out of scope for this pass -- documented
        # no-op, not silently pretending to search.
        return []

    async def delete_node(self, tenant_id: UUID, node_id: str) -> bool:
        return bool(self.nodes.pop((str(tenant_id), node_id), None))

    async def health_check(self) -> bool:
        return True
