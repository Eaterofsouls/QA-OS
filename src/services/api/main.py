"""FastAPI entrypoint for the QA Operating System API.

Wires the real routes needed for the qualifying-prototype vertical slice:
  POST /requirements/{id}/assess                       -> Module 1 (RequirementRiskAssessor)
  POST /requirements/{id}/generate-tests                -> Module 2 (TestSuiteGenerator)
  GET  /requirements/{id}/tests                          -> reads generated test cases + review
                                                             status back out of the KG
  POST /requirements/{id}/tests/{test_case_id}/review    -> Module 3 (HumanReviewGate)
  GET  /requirements/{id}/cost                            -> real logged token/cost entries
                                                             from CostLedger for this requirement

All routes call real module logic against the real (Sprint-0 in-memory stub, or
Neo4j if NEO4J_URI is set) KG client. Modules 1/2 additionally call a real
LLM via the extraction backbone -- which now also logs real token usage and
an estimated cost to CostLedger for every such call (see
packages/llm-gateway-client/ledger.py); Module 3 is a human decision and
makes no LLM call at all -- no mock/hardcoded response data anywhere in this
file.

/assess additionally has retrieval-based memory: before building its
prompt, Module 1 pulls similar past requirements for the tenant (TF-IDF
cosine similarity over stored Requirement text -- see
packages/kg-client/similarity.py) and injects their real stored risk
assessment + human review decision as few-shot context. This is
retrieval-augmented PROMPTING, not model fine-tuning/training -- see
README.md §6/§7/§8. AssessResponse.retrieval reports what was actually
used, for the UI (apps/web/src/app/page.tsx) to display honestly.
"""
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from extraction import ExtractionError, get_extraction_backbone
from kg_client import KGClientInterface, get_client
from llm_gateway_client import LLMGatewayError
from llm_gateway_client.ledger import get_cost_ledger
from module_01 import (
    RequirementRiskAssessor,
    RiskAssessmentInput,
    RiskAssessmentOutput,
    RetrievalContext,
)
from module_02 import TestGenerationInput, TestGenerationOutput, TestSuiteGenerator
from module_03 import HumanReviewGate, ReviewDecision

app = FastAPI(title="QA Operating System API")

# Single KG client instance for the process lifetime. get_client() returns
# the Sprint-0 in-memory KGClientStub unless NEO4J_URI is set (see
# kg-client/client.py) -- swapping to real Neo4j needs no code change here.
_kg_client: KGClientInterface = get_client()


def get_kg_client() -> KGClientInterface:
    return _kg_client


class AssessRequest(BaseModel):
    tenant_id: str
    requirement_text: str
    source_tool: str = "manual"


class GenerateTestsRequest(BaseModel):
    tenant_id: str


class TestCaseReviewRequest(BaseModel):
    tenant_id: str
    reviewer_id: str
    decision: Literal["approved", "rejected"]
    note: str | None = None


class TestCaseReviewResponse(BaseModel):
    test_case_id: str
    requirement_id: str
    status: str
    reviewer_id: str
    note: str | None = None
    review_request_id: str


class TestCaseWithReview(BaseModel):
    id: str
    title: str
    description: str
    steps: list[str]
    expected_result: str
    test_type: str
    priority: str
    status: str
    reviewer_id: str | None = None
    review_note: str | None = None


class RequirementTestsResponse(BaseModel):
    requirement_id: str
    test_cases: list[TestCaseWithReview]


class CostLedgerEntryResponse(BaseModel):
    id: str
    tenant_id: str
    requirement_id: str | None
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    usage_reported: bool
    estimated_cost_usd: float | None
    cost_basis: str | None
    timestamp: str


class AssessResponse(RiskAssessmentOutput):
    """Everything RiskAssessmentOutput has (this is exactly the schema the
    LLM was asked to produce, and exactly what gets persisted to the KG as
    the RiskAssessment node) plus one additive field: `retrieval`, a real
    readout of whether -- and which -- past requirements' real stored
    outcomes were pulled in and injected into the prompt as few-shot
    context before this assessment was made.

    This is retrieval-based memory / retrieval-augmented PROMPTING: real
    past requirement text plus real stored risk/review outcomes, looked up
    by TF-IDF cosine similarity and inserted into the prompt text itself.
    It is NOT model fine-tuning or retraining -- no training data, no
    weight updates, nothing of the sort exists anywhere in this repository.
    See README.md §6/§7/§8 and modules/module-01/assessor.py.
    """
    retrieval: RetrievalContext


class RequirementCostResponse(BaseModel):
    requirement_id: str
    entries: list[CostLedgerEntryResponse]
    # Aggregates are only computed over entries with real numbers -- if any
    # entry has an unknown token count or unpriced model, the corresponding
    # total is None rather than silently undercounting.
    total_prompt_tokens: int | None
    total_completion_tokens: int | None
    total_estimated_cost_usd: float | None


class GraphNode(BaseModel):
    """One real KG node, as returned by get_node()/get_related() -- the full
    properties dict is passed through unfiltered (tenant_id included) so the
    frontend's node-click side panel can show exactly what's really stored,
    not a curated subset."""
    id: str
    label: str
    properties: dict


class GraphEdge(BaseModel):
    """One inferred relationship. There is no real edge store yet (see
    kg-client/stub.py's create_relationship() TODO) -- `type` is inferred
    from *which* foreign-key-style field on the target node actually
    matched the source id in get_related(), not guessed or hardcoded per
    node label."""
    source: str
    target: str
    type: str


class RequirementGraphResponse(BaseModel):
    requirement_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@app.post("/requirements/{requirement_id}/assess", response_model=AssessResponse)
async def assess_requirement(
    requirement_id: str,
    body: AssessRequest,
    kg: KGClientInterface = Depends(get_kg_client),
) -> AssessResponse:
    tenant_uuid = uuid.UUID(body.tenant_id)

    # Persist the requirement itself first. Module 1's assessor only ever
    # calls get_related() on this id -- nothing upserted the Requirement
    # node before now, so there was nothing real to retrieve later. This
    # also makes the requirement's text available to find_similar_requirements()
    # for the *next* requirement assessed for this tenant.
    await kg.upsert_node(tenant_uuid, "Requirement", {
        "id": requirement_id,
        "text": body.requirement_text,
        "source_tool": body.source_tool,
    })

    assessor = RequirementRiskAssessor(
        kg_client=kg,
        extraction_backbone=get_extraction_backbone(body.tenant_id),
    )
    try:
        assessment = await assessor.assess(RiskAssessmentInput(
            requirement_id=requirement_id,
            tenant_id=body.tenant_id,
            requirement_text=body.requirement_text,
            source_tool=body.source_tool,
        ))
    except (LLMGatewayError, ExtractionError) as exc:
        # Real failures surface as a real error -- see Step 2: these used to
        # be swallowed and replaced with a fake empty result.
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # assess() always sets this before it can raise, so this is only a
    # defensive fallback for a backend that doesn't set it at all -- never
    # silently fabricated retrieval info.
    retrieval = assessor.last_retrieval_context or RetrievalContext(
        similarity_threshold=0.0, similar_requirements=[]
    )
    return AssessResponse(**assessment.model_dump(), retrieval=retrieval)


@app.post("/requirements/{requirement_id}/generate-tests", response_model=TestGenerationOutput)
async def generate_tests(
    requirement_id: str,
    body: GenerateTestsRequest,
    kg: KGClientInterface = Depends(get_kg_client),
) -> TestGenerationOutput:
    tenant_uuid = uuid.UUID(body.tenant_id)

    requirement = await kg.get_node(tenant_uuid, requirement_id)
    if requirement is None:
        raise HTTPException(
            status_code=404,
            detail=f"Requirement '{requirement_id}' not found for this tenant. Call /assess first.",
        )

    # Pull the risk assessment back out of the KG (this is the "actually
    # persisted and retrievable via the KG client" part of the vertical
    # slice -- not passed through from the client, and not re-computed).
    related = await kg.get_related(tenant_uuid, requirement_id)
    risk_nodes = [r for r in related if r.get("label") == "RiskAssessment"]
    if not risk_nodes:
        raise HTTPException(
            status_code=409,
            detail=f"No risk assessment found for '{requirement_id}'. Call /assess first.",
        )
    risk_assessment = RiskAssessmentOutput(**risk_nodes[0])

    generator = TestSuiteGenerator(
        kg_client=kg,
        extraction_backbone=get_extraction_backbone(body.tenant_id),
    )
    try:
        return await generator.generate(TestGenerationInput(
            requirement_id=requirement_id,
            tenant_id=body.tenant_id,
            requirement_text=requirement["text"],
            risk_assessment=risk_assessment,
        ))
    except (LLMGatewayError, ExtractionError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/requirements/{requirement_id}/tests", response_model=RequirementTestsResponse)
async def list_requirement_tests(
    requirement_id: str,
    tenant_id: str = Query(..., description="Tenant UUID that owns this requirement."),
    kg: KGClientInterface = Depends(get_kg_client),
) -> RequirementTestsResponse:
    tenant_uuid = uuid.UUID(tenant_id)

    requirement = await kg.get_node(tenant_uuid, requirement_id)
    if requirement is None:
        raise HTTPException(
            status_code=404,
            detail=f"Requirement '{requirement_id}' not found for this tenant. Call /assess first.",
        )

    # Mirrors generate_tests()'s pattern: read the current state back from
    # the KG rather than trusting anything the client claims. get_related()
    # already returns each TestCase's KG-assigned "id" (module-02's
    # generator.py never set one explicitly, so KGClientStub.upsert_node
    # generated one and get_related() surfaces it via the storage key --
    # this is the id the review route below expects).
    related = await kg.get_related(tenant_uuid, requirement_id)
    test_case_nodes = [r for r in related if r.get("label") == "TestCase"]

    return RequirementTestsResponse(
        requirement_id=requirement_id,
        test_cases=[
            TestCaseWithReview(
                id=node["id"],
                title=node["title"],
                description=node["description"],
                steps=node["steps"],
                expected_result=node["expected_result"],
                test_type=node["test_type"],
                priority=node["priority"],
                status=node.get("status", "draft"),
                reviewer_id=node.get("reviewer_id"),
                review_note=node.get("review_note"),
            )
            for node in test_case_nodes
        ],
    )


@app.get("/requirements/{requirement_id}/cost", response_model=RequirementCostResponse)
async def get_requirement_cost(
    requirement_id: str,
    tenant_id: str = Query(..., description="Tenant UUID that owns this requirement."),
) -> RequirementCostResponse:
    """Real logged token/cost entries for this requirement -- one entry per
    real LLM call made through extraction/backbone.py's ExtractionBackbone
    while assessing risk (/assess) or generating tests (/generate-tests)
    for it. Nothing here is computed client-side or estimated on the fly;
    this reads back exactly what CostLedger.record_call() wrote at call
    time (see packages/llm-gateway-client/ledger.py).

    Does not require the requirement to exist in the KG -- an unknown
    requirement_id just returns zero entries (there's nothing to 404 on;
    the ledger is keyed independently of the KG).
    """
    ledger = get_cost_ledger()
    entries = ledger.get_entries_for_requirement(tenant_id, requirement_id)

    total_prompt_tokens = None
    total_completion_tokens = None
    total_estimated_cost_usd = None
    if entries:
        prompt_vals = [e.prompt_tokens for e in entries]
        completion_vals = [e.completion_tokens for e in entries]
        cost_vals = [e.estimated_cost_usd for e in entries]
        if all(v is not None for v in prompt_vals):
            total_prompt_tokens = sum(prompt_vals)
        if all(v is not None for v in completion_vals):
            total_completion_tokens = sum(completion_vals)
        if all(v is not None for v in cost_vals):
            total_estimated_cost_usd = round(sum(cost_vals), 6)

    return RequirementCostResponse(
        requirement_id=requirement_id,
        entries=[CostLedgerEntryResponse(**e.to_dict()) for e in entries],
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        total_estimated_cost_usd=total_estimated_cost_usd,
    )


@app.post(
    "/requirements/{requirement_id}/tests/{test_case_id}/review",
    response_model=TestCaseReviewResponse,
)
async def review_test_case(
    requirement_id: str,
    test_case_id: str,
    body: TestCaseReviewRequest,
    kg: KGClientInterface = Depends(get_kg_client),
) -> TestCaseReviewResponse:
    tenant_uuid = uuid.UUID(body.tenant_id)

    requirement = await kg.get_node(tenant_uuid, requirement_id)
    if requirement is None:
        raise HTTPException(
            status_code=404,
            detail=f"Requirement '{requirement_id}' not found for this tenant. Call /assess first.",
        )

    test_case = await kg.get_node(tenant_uuid, test_case_id)
    if test_case is None or test_case.get("requirement_id") != requirement_id:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Test case '{test_case_id}' not found for requirement "
                f"'{requirement_id}'. Call /generate-tests first."
            ),
        )

    # HumanReviewGate's real interface (module_03/gate.py) is built around a
    # ReviewRequest batching one-or-more test_case_ids, not a single-test-case
    # review call -- there's no smaller method that fits this route directly.
    # Rather than redesigning it, this uses the real class exactly as
    # written: create a review request scoped to just this one test case,
    # then submit a decision against it. See README.md §6/§8 for why this
    # shape was chosen instead of adding a new bespoke method.
    gate = HumanReviewGate(kg_client=kg)
    review_request = await gate.create_review_request(
        tenant_id=body.tenant_id,
        requirement_id=requirement_id,
        test_case_ids=[test_case_id],
        risk_context=body.note or "",
    )
    decision = ReviewDecision(
        review_request_id=review_request.id,
        decision=body.decision,
        reviewer_id=body.reviewer_id,
        approved_test_case_ids=[test_case_id] if body.decision == "approved" else [],
        note=body.note,
    )
    ok = await gate.submit_decision(decision)
    if not ok:
        # Can only happen if the review request vanished between the two
        # calls above -- surfaced honestly rather than assumed impossible.
        raise HTTPException(status_code=409, detail="Review request could not be recorded.")

    updated = await kg.get_node(tenant_uuid, test_case_id)
    return TestCaseReviewResponse(
        test_case_id=test_case_id,
        requirement_id=requirement_id,
        status=updated["status"],
        reviewer_id=updated["reviewer_id"],
        note=updated.get("review_note"),
        review_request_id=review_request.id,
    )


@app.get("/requirements/{requirement_id}/graph", response_model=RequirementGraphResponse)
async def get_requirement_graph(
    requirement_id: str,
    tenant_id: str = Query(..., description="Tenant UUID that owns this requirement."),
    kg: KGClientInterface = Depends(get_kg_client),
) -> RequirementGraphResponse:
    """Real nodes + edges for one requirement, for apps/web/src/app/graph/page.tsx.

    The Requirement node plus everything get_related() finds for it (real
    RiskAssessment / TestCase nodes, each carrying its real stored
    properties -- risk score, test steps, Module 3 review status, etc).
    There is still no real edge store (see kg-client/stub.py's
    create_relationship() TODO), so an edge's `type` is inferred from
    exactly which of get_related()'s matched fields fired for that node,
    mirroring get_related()'s own `reference_fields` order
    (requirement_id, covers_requirement, from_id/to_id) rather than being
    guessed from the node's label.
    """
    tenant_uuid = uuid.UUID(tenant_id)

    requirement = await kg.get_node(tenant_uuid, requirement_id)
    if requirement is None:
        raise HTTPException(
            status_code=404,
            detail=f"Requirement '{requirement_id}' not found for this tenant. Call /assess first.",
        )

    nodes = [GraphNode(id=requirement_id, label="Requirement", properties=requirement)]
    edges: list[GraphEdge] = []

    related = await kg.get_related(tenant_uuid, requirement_id)
    for node in related:
        node_id = node["id"]
        label = node["label"]
        nodes.append(GraphNode(id=node_id, label=label, properties=node))

        if node.get("requirement_id") == requirement_id:
            # Both RiskAssessment and TestCase nodes link back via this same
            # field (see get_related()'s docstring) -- disambiguate by label
            # only for the edge's semantic name, not for whether it matched.
            edge_type = "ASSESSES" if label == "RiskAssessment" else "COVERS"
        elif node.get("covers_requirement") == requirement_id:
            edge_type = "COVERS"
        elif node.get("from_id") == requirement_id or node.get("to_id") == requirement_id:
            # fixtures.py-style explicit relationships carry their own
            # rel_type; fall back to a generic label if absent.
            edge_type = node.get("rel_type") or "RELATED_TO"
        else:
            edge_type = "RELATED_TO"

        edges.append(GraphEdge(source=requirement_id, target=node_id, type=edge_type))

    return RequirementGraphResponse(requirement_id=requirement_id, nodes=nodes, edges=edges)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "kg_backend": type(_kg_client).__name__}
