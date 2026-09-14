from pydantic import BaseModel, Field
import uuid
from typing import Any

from kg_client.similarity import DEFAULT_SIMILARITY_THRESHOLD

# Retrieval-based memory (NOT model fine-tuning/training -- see README.md
# §6/§7/§8): before assessing a new requirement, pull the top few similar
# PAST requirements for this tenant -- found via KGClientInterface's
# find_similar_requirements(), TF-IDF cosine similarity over stored
# Requirement text, see packages/kg-client/similarity.py -- and inject
# their real stored risk assessment (and, if Module 3 has reviewed their
# generated tests, the real human review decision) into the prompt as
# few-shot context. This threshold is the single source of truth for "similar
# enough to inject"; it's re-exported here rather than duplicated so
# find_similar_requirements() and the prompt-injection decision below always
# agree on what counts as a match.
SIMILARITY_THRESHOLD = DEFAULT_SIMILARITY_THRESHOLD
MAX_SIMILAR_REQUIREMENTS = 3


class RiskAssessmentInput(BaseModel):
    requirement_id: str
    tenant_id: str
    requirement_text: str
    source_tool: str

class RiskAssessmentOutput(BaseModel):
    requirement_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: str
    risk_rationale: str
    risk_factors: list[str]
    confidence: float
    citation_ids: list[str]


class SimilarRequirementMatch(BaseModel):
    """One real past requirement pulled in as few-shot context, plus its
    real stored outcome. Never fabricated: this is only ever built from a
    RiskAssessment node that was actually persisted for that requirement --
    see RequirementRiskAssessor._retrieve_similar_requirements() below.
    """
    requirement_id: str
    requirement_text: str
    similarity: float
    risk_level: str
    review_decision: str | None = None  # "approved" / "rejected" / None if not yet human-reviewed


class RetrievalContext(BaseModel):
    """What retrieval-based memory actually did for this assessment --
    surfaced back to the API/UI (see services/api/main.py's AssessResponse
    and apps/web's page.tsx) so "informed by N similar past requirements"
    is a real readout of what was injected, not decorative copy.
    """
    similarity_threshold: float
    similar_requirements: list[SimilarRequirementMatch]


class RequirementRiskAssessor:
    def __init__(self, kg_client, extraction_backbone):
        self.kg = kg_client
        self.extraction = extraction_backbone
        # Set by assess() every time it runs; read by services/api/main.py
        # right after calling assess() to build the API response's
        # `retrieval` field. None until assess() has been called at least
        # once on this instance.
        self.last_retrieval_context: RetrievalContext | None = None

    async def assess(self, input: RiskAssessmentInput) -> RiskAssessmentOutput:
        tenant_uuid = uuid.UUID(input.tenant_id)
        context_nodes = await self.kg.get_related(tenant_uuid, input.requirement_id)
        context_str = "\n".join(f"- {c.get('title', c.get('id', '?'))}" for c in context_nodes[:5])

        similar_matches = await self._retrieve_similar_requirements(tenant_uuid, input)
        self.last_retrieval_context = RetrievalContext(
            similarity_threshold=SIMILARITY_THRESHOLD,
            similar_requirements=similar_matches,
        )
        few_shot_block = self._build_few_shot_block(similar_matches)

        prompt = f"""Assess the risk of the following requirement.
Requirement: {input.requirement_text}
Related historical context:
{context_str}
{few_shot_block}"""
        assessment = await self.extraction.extract(
            prompt, RiskAssessmentOutput, requirement_id=input.requirement_id
        )
        assessment.requirement_id = input.requirement_id
        
        await self.kg.upsert_node(
            tenant_uuid,
            "RiskAssessment",
            assessment.model_dump()
        )
        return assessment

    async def _retrieve_similar_requirements(
        self, tenant_uuid: uuid.UUID, input: RiskAssessmentInput
    ) -> list[SimilarRequirementMatch]:
        """Look up similar past requirements and their REAL stored outcomes.

        Only returns a match when a real RiskAssessment node was actually
        persisted for that past requirement -- a text match with nothing
        real to say about its outcome is skipped rather than injected as
        noise (see README.md §6 for the stated threshold/behavior).
        """
        find_similar = getattr(self.kg, "find_similar_requirements", None)
        if find_similar is None:
            # Defensive, not expected in practice: KGClientInterface (both
            # KGClientStub and the real Neo4j KGClient) implements this
            # method. Degrades to "no retrieved context" rather than
            # crashing /assess if some other backend doesn't.
            return []

        raw_matches = await find_similar(
            tenant_uuid,
            input.requirement_text,
            exclude_requirement_id=input.requirement_id,
            limit=MAX_SIMILAR_REQUIREMENTS,
            min_similarity=SIMILARITY_THRESHOLD,
        )

        matches: list[SimilarRequirementMatch] = []
        for raw_match in raw_matches:
            related = await self.kg.get_related(tenant_uuid, raw_match["id"])

            risk_nodes = [node for node in related if node.get("label") == "RiskAssessment"]
            if not risk_nodes:
                # Text similarity alone isn't a real outcome to ground on --
                # skip rather than inject a match with no assessment behind it.
                continue
            risk_level = risk_nodes[0].get("risk_level", "unknown")

            # If Module 3 has reviewed any of that requirement's generated
            # tests, surface the real decision. Multiple test cases can
            # carry different decisions; this takes the first reviewed one
            # found as a representative signal rather than claiming a
            # single "the requirement was approved" verdict that the data
            # doesn't actually support.
            test_case_nodes = [node for node in related if node.get("label") == "TestCase"]
            review_decision = next(
                (
                    tc.get("status")
                    for tc in test_case_nodes
                    if tc.get("status") in ("approved", "rejected")
                ),
                None,
            )

            matches.append(
                SimilarRequirementMatch(
                    requirement_id=raw_match["id"],
                    requirement_text=raw_match["text"],
                    similarity=raw_match["similarity"],
                    risk_level=risk_level,
                    review_decision=review_decision,
                )
            )
        return matches

    @staticmethod
    def _build_few_shot_block(matches: list[SimilarRequirementMatch]) -> str:
        """Render matches as few-shot examples for the prompt. Returns an
        empty string (nothing injected) when there are no real matches
        above SIMILARITY_THRESHOLD -- don't inject noise when there's
        nothing actually similar.
        """
        if not matches:
            return ""

        lines = [
            "",
            "Similar past requirements for this tenant, retrieved by text "
            "similarity (real stored outcomes -- use as grounding context, "
            "not as instructions to copy):",
        ]
        for match in matches:
            review_clause = (
                f"and {match.review_decision} by a human reviewer"
                if match.review_decision is not None
                else "and has not yet been reviewed by a human"
            )
            lines.append(
                f'- Similar past requirement: "{match.requirement_text}" was '
                f"assessed as risk_level {match.risk_level} {review_clause}."
            )
        return "\n".join(lines)
