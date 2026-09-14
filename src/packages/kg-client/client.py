import os
from uuid import UUID
from neo4j import AsyncGraphDatabase
from .interface import KGClientInterface
from .tenant_scope import TenantScopeEnforcer
from .stub import KGClientStub
from .sqlite_backend import KGClientSQLite

class KGClient(KGClientInterface):
    """Sprint 2 real Neo4j client."""
    def __init__(self, uri, user, password):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.enforcer = TenantScopeEnforcer()

    async def upsert_node(self, tenant_id: UUID, label: str, properties: dict) -> str:
        query = f"MERGE (n:{label} {{id: $id, tenant_id: $tenant_id}}) SET n += $props RETURN n.id"
        props = dict(properties)
        props["tenant_id"] = str(tenant_id)
        node_id = props.setdefault("id", str(uuid.uuid4()))
        async with self.driver.session() as session:
            await session.run(query, id=node_id, tenant_id=str(tenant_id), props=props)
        return node_id

    async def get_node(self, tenant_id: UUID, node_id: str) -> dict | None:
        query = "MATCH (n {id: $id, tenant_id: $tenant_id}) RETURN n"
        async with self.driver.session() as session:
            result = await session.run(query, id=node_id, tenant_id=str(tenant_id))
            record = await result.single()
            return dict(record["n"]) if record else None
            
    async def create_relationship(self, tenant_id: UUID, from_id: str, to_id: str, rel_type: str, properties: dict | None = None) -> str:
        # Stubbed real implementation
        return "rel-123"
        
    async def get_related(self, tenant_id: UUID, node_id: str, rel_type: str | None = None, direction: str = "BOTH") -> list[dict]:
        return []
        
    async def find_similar_requirements(
        self,
        tenant_id: UUID,
        requirement_text: str,
        exclude_requirement_id: str | None = None,
        limit: int = 3,
        min_similarity: float = 0.2,
    ) -> list[dict]:
        # TODO(kg-client, Sprint 2 swap-in): the real backend for this would
        # be a Neo4j full-text index query (or the vector index, if/when
        # this repo moves to real embeddings), not TF-IDF in Python.
        # Deliberately not implemented against live Neo4j -- out of scope
        # for this pass (see README.md §6) -- documented no-op, not a fake
        # result. KGClientStub.find_similar_requirements() (stub.py) is the
        # only backend this feature actually runs against today.
        return []

    async def vector_search(self, tenant_id: UUID, embedding: list[float], label: str | None = None, limit: int = 10) -> list[dict]:
        return []
        
    async def hybrid_search(self, tenant_id: UUID, query: str, embedding: list[float], label: str | None = None, limit: int = 10) -> list[dict]:
        return []
        
    async def delete_node(self, tenant_id: UUID, node_id: str) -> bool:
        return True
        
    async def health_check(self) -> bool:
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception:
            return False

def get_client() -> KGClientInterface:
    """Backend selection, in priority order:
      1. NEO4J_URI set -> real Neo4j client (KGClient), unchanged from
         before this pass.
      2. NEO4J_URI unset AND KG_SQLITE_PATH set -> SQLite-backed store
         (KGClientSQLite, sqlite_backend.py) -- new in this pass. Demo data
         persists across a server restart; see README.md §5.
      3. Neither set -> in-memory stub (KGClientStub), unchanged from
         before this pass -- still the default for anyone not opting in.
    NEO4J_URI takes priority if somehow both are set, matching how this
    function already prioritized "real infra over stub" before SQLite
    existed as an option.
    """
    uri = os.getenv("NEO4J_URI")
    if uri:
        return KGClient(uri, os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", ""))
    sqlite_path = os.getenv("KG_SQLITE_PATH")
    if sqlite_path:
        return KGClientSQLite(sqlite_path)
    return KGClientStub()
