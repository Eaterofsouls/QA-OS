from pydantic import BaseModel
import uuid

class QueryRequest(BaseModel):
    tenant_id: str
    query_text: str

class KnowledgeGraphQueryService:
    def __init__(self, kg_client):
        self.kg = kg_client
        
    async def search(self, request: QueryRequest) -> list:
        # Stub implementation
        return await self.kg.get_related(uuid.UUID(request.tenant_id), "search-root")
