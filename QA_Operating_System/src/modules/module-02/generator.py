from pydantic import BaseModel
import uuid
from module_01.assessor import RiskAssessmentOutput

class TestGenerationInput(BaseModel):
    requirement_id: str
    tenant_id: str
    requirement_text: str
    risk_assessment: RiskAssessmentOutput

class GeneratedTestCase(BaseModel):
    title: str
    description: str
    steps: list[str]
    expected_result: str
    test_type: str
    priority: str

class TestGenerationOutput(BaseModel):
    requirement_id: str
    test_cases: list[GeneratedTestCase]
    generation_confidence: float

class TestSuiteGenerator:
    def __init__(self, kg_client, extraction_backbone):
        self.kg = kg_client
        self.extraction = extraction_backbone
        
    async def generate(self, input: TestGenerationInput) -> TestGenerationOutput:
        prompt = f"""Generate test cases for this requirement.
Requirement: {input.requirement_text}
Risk Level: {input.risk_assessment.risk_level}
"""
        output = await self.extraction.extract(
            prompt, TestGenerationOutput, requirement_id=input.requirement_id
        )
        output.requirement_id = input.requirement_id
        
        for tc in output.test_cases:
            tc_data = tc.model_dump()
            tc_data["requirement_id"] = input.requirement_id
            tc_data["status"] = "draft"
            await self.kg.upsert_node(uuid.UUID(input.tenant_id), "TestCase", tc_data)
            
        return output
