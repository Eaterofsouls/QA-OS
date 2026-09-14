from pydantic import BaseModel

class TriageInput(BaseModel):
    tenant_id: str
    observation_id: str
    defect_description: str
    test_case_id: str

class TriageClassification(BaseModel):
    classification: str
    confidence: float
    rationale: str
    suggested_priority: str
    suggested_decision: str

class DefectTriageService:
    def __init__(self, kg_client, extraction):
        self.kg = kg_client
        self.extraction = extraction
        
    async def triage(self, input: TriageInput) -> TriageClassification:
        prompt = f"Triage this defect: {input.defect_description}"
        res = await self.extraction.extract(prompt, TriageClassification)
        return res
