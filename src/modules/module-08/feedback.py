from pydantic import BaseModel
import uuid

class FeedbackInput(BaseModel):
    tenant_id: str
    incident_title: str

class FeedbackLoopService:
    def __init__(self, kg_client):
        self.kg = kg_client
        
    async def process_incident(self, input: FeedbackInput):
        await self.kg.upsert_node(
            uuid.UUID(input.tenant_id),
            "ProductionIncident",
            {"title": input.incident_title}
        )
