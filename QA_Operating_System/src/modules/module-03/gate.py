from pydantic import BaseModel, Field
from uuid import uuid4, UUID
import datetime

class ReviewRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    requirement_id: str
    test_case_ids: list[str]
    review_context: str
    status: str = "pending"
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class ReviewDecision(BaseModel):
    review_request_id: str
    decision: str
    reviewer_id: str
    approved_test_case_ids: list[str]
    # Aug 2026 engineering pass: additive field, optional so any existing
    # caller that doesn't pass it still validates. Lets a reviewer attach
    # free-text context (e.g. why something was rejected) that main.py's
    # new review route can surface back to the client.
    note: str | None = None

class HumanReviewGate:
    def __init__(self, kg_client):
        self.kg = kg_client
        # NOTE: pending_reviews is process-memory only (lost on restart),
        # same Sprint-0-grade tradeoff as KGClientStub itself. Fine for the
        # current single-process vertical slice; would need to move to the
        # KG (or a real queue) before this survives multiple API replicas.
        self.pending_reviews = {}
        
    async def create_review_request(self, tenant_id, requirement_id, test_case_ids, risk_context) -> ReviewRequest:
        req = ReviewRequest(
            tenant_id=tenant_id,
            requirement_id=requirement_id,
            test_case_ids=test_case_ids,
            review_context=risk_context
        )
        self.pending_reviews[req.id] = req
        return req
        
    async def submit_decision(self, decision: ReviewDecision) -> bool:
        """Record a reviewer's decision for a previously-created review request.

        Aug 2026 engineering pass fix: this previously did two things wrong,
        matching the same "looks wired, does nothing real" pattern found
        elsewhere in the repo (see README.md §8):
          1. It returned `True` unconditionally, even when
             `decision.review_request_id` didn't match any request in
             `pending_reviews` -- a silent no-op reported as success.
          2. `self.kg` was accepted in `__init__` and never referenced again
             anywhere in the class -- the decision only ever lived in the
             in-memory `pending_reviews` dict, so nothing else (e.g. a GET
             route reading test cases back out of the KG) could ever see it.

        Both are fixed here: a missing/unknown review request now returns
        False (so a caller like main.py can raise an honest 404/409 instead
        of pretending it worked), and each reviewed TestCase's KG node is
        updated in place with its real status/reviewer/note -- read back via
        the same kg.get_node/upsert_node pattern module-01/module-02 already
        use to persist their own output.
        """
        req = self.pending_reviews.get(decision.review_request_id)
        if req is None:
            return False
        req.status = decision.decision

        tenant_uuid = UUID(req.tenant_id)
        for tc_id in req.test_case_ids:
            node = await self.kg.get_node(tenant_uuid, tc_id)
            if node is None:
                # Test case vanished between review-request creation and
                # decision submission -- skip it rather than fabricating a
                # node; the caller can detect this by re-reading the node.
                continue
            node["id"] = tc_id
            node["status"] = "approved" if tc_id in decision.approved_test_case_ids else "rejected"
            node["reviewer_id"] = decision.reviewer_id
            node["review_note"] = decision.note
            await self.kg.upsert_node(tenant_uuid, "TestCase", node)
        return True
