from pydantic import BaseModel

class GoNoGoRequest(BaseModel):
    tenant_id: str
    release_version: str
    requirement_ids: list[str]

class GoNoGoRecommendation(BaseModel):
    tenant_id: str
    release_version: str
    recommendation: str
    confidence: float
    rationale: str

class ReleaseReadinessService:
    def __init__(self, kg_client, extraction):
        self.kg = kg_client
        self.extraction = extraction
        
    async def analyze(self, request: GoNoGoRequest) -> GoNoGoRecommendation:
        prompt = f"Analyze release readiness for {request.release_version}."
        return await self.extraction.extract(prompt, GoNoGoRecommendation)
