"""
Standalone verification for Step 4 (Module 3 / Review Gate wiring).

Run from services/api/ with: uv run python3 verify_step4_module3.py

Same approach as verify_step3.py: monkeypatches main.get_extraction_backbone
so the two LLM-backed routes (/assess, /generate-tests) get a canned response
instead of a real network call (no LLM endpoint reachable in this
environment). Module 3's route makes NO LLM call at all -- it's a human
decision -- so the review/list routes below are exercised completely
unmocked, hitting real FastAPI routing, the real HumanReviewGate class, and
real KGClientStub persistence + retrieval.
"""
import uuid

import main as main_module
from extraction import ExtractionBackbone
from fastapi.testclient import TestClient

RISK_JSON = (
    '{"requirement_id": "placeholder", "risk_score": 0.82, "risk_level": "high", '
    '"risk_rationale": "Auth changes affect all users", '
    '"risk_factors": ["auth", "external-facing"], "confidence": 0.9, "citation_ids": []}'
)
TESTS_JSON = (
    '{"requirement_id": "placeholder", "test_cases": ['
    '{"title": "Reject invalid token", "description": "d", "steps": ["s1"], '
    '"expected_result": "401", "test_type": "negative", "priority": "high"},'
    '{"title": "Refresh token before expiry", "description": "d2", "steps": ["s1", "s2"], '
    '"expected_result": "session extended", "test_type": "positive", "priority": "medium"}'
    '], "generation_confidence": 0.85}'
)


class FakeLLM:
    def __init__(self, content):
        self._content = content

    async def complete(self, model, messages, **kwargs):
        return {"choices": [{"message": {"content": self._content}}]}


def fake_get_extraction_backbone(tenant_id: str) -> ExtractionBackbone:
    fake_get_extraction_backbone.calls += 1
    content = RISK_JSON if fake_get_extraction_backbone.calls == 1 else TESTS_JSON
    return ExtractionBackbone(llm_client=FakeLLM(content))


fake_get_extraction_backbone.calls = 0
main_module.get_extraction_backbone = fake_get_extraction_backbone

client = TestClient(main_module.app)
tenant_id = str(uuid.uuid4())
requirement_id = "req-e2e-module3-001"

# 1. /assess (prerequisite -- Module 1, unchanged, re-verified here as setup)
resp = client.post(
    f"/requirements/{requirement_id}/assess",
    json={"tenant_id": tenant_id, "requirement_text": "Users must log in via OAuth2.", "source_tool": "manual"},
)
print("POST /assess ->", resp.status_code)
assert resp.status_code == 200

# 2. /generate-tests (prerequisite -- Module 2, unchanged, re-verified here as setup)
resp = client.post(f"/requirements/{requirement_id}/generate-tests", json={"tenant_id": tenant_id})
print("POST /generate-tests ->", resp.status_code)
assert resp.status_code == 200
generated = resp.json()
assert len(generated["test_cases"]) == 2

# 3. GET /requirements/{id}/tests -- real KG read-back, both test cases
#    should be present with KG-assigned ids and status "draft".
resp = client.get(f"/requirements/{requirement_id}/tests", params={"tenant_id": tenant_id})
print("GET /tests ->", resp.status_code, resp.json())
assert resp.status_code == 200
listed = resp.json()["test_cases"]
assert len(listed) == 2
assert all(tc["status"] == "draft" for tc in listed)
assert all(tc["id"] for tc in listed)  # KG-assigned ids present
tc_reject, tc_approve = listed[0], listed[1]

# 4. GET /tests for a requirement with no test cases generated yet -> 404,
#    not a fake empty list, matching the existing 404/409 pattern.
resp = client.get("/requirements/req-never-assessed/tests", params={"tenant_id": tenant_id})
print("GET /tests (unknown requirement) ->", resp.status_code, resp.json())
assert resp.status_code == 404

# 5. POST review -> approve one test case
resp = client.post(
    f"/requirements/{requirement_id}/tests/{tc_approve['id']}/review",
    json={"tenant_id": tenant_id, "reviewer_id": "qa-lead-jane", "decision": "approved", "note": "Looks solid."},
)
print("POST /review (approve) ->", resp.status_code, resp.json())
assert resp.status_code == 200
approve_result = resp.json()
assert approve_result["status"] == "approved"
assert approve_result["reviewer_id"] == "qa-lead-jane"
assert approve_result["note"] == "Looks solid."

# 6. POST review -> reject the other test case
resp = client.post(
    f"/requirements/{requirement_id}/tests/{tc_reject['id']}/review",
    json={"tenant_id": tenant_id, "reviewer_id": "qa-lead-jane", "decision": "rejected", "note": "Missing edge case."},
)
print("POST /review (reject) ->", resp.status_code, resp.json())
assert resp.status_code == 200
reject_result = resp.json()
assert reject_result["status"] == "rejected"

# 7. GET /tests again -- both decisions must be visible from a completely
#    fresh read (not the POST response, an independent read-back from the KG).
resp = client.get(f"/requirements/{requirement_id}/tests", params={"tenant_id": tenant_id})
print("GET /tests (after review) ->", resp.status_code, resp.json())
assert resp.status_code == 200
final = {tc["id"]: tc for tc in resp.json()["test_cases"]}
assert final[tc_approve["id"]]["status"] == "approved"
assert final[tc_approve["id"]]["reviewer_id"] == "qa-lead-jane"
assert final[tc_reject["id"]]["status"] == "rejected"
assert final[tc_reject["id"]]["review_note"] == "Missing edge case."

# 8. Reviewing a test case that doesn't belong to this requirement -> 404,
#    not a silent no-op.
resp = client.post(
    f"/requirements/{requirement_id}/tests/not-a-real-test-case-id/review",
    json={"tenant_id": tenant_id, "reviewer_id": "qa-lead-jane", "decision": "approved"},
)
print("POST /review (unknown test case) ->", resp.status_code, resp.json())
assert resp.status_code == 404

# 9. Invalid decision value -> honest 422 from Pydantic's Literal validation,
#    not silently accepted.
resp = client.post(
    f"/requirements/{requirement_id}/tests/{tc_approve['id']}/review",
    json={"tenant_id": tenant_id, "reviewer_id": "qa-lead-jane", "decision": "maybe"},
)
print("POST /review (invalid decision) ->", resp.status_code)
assert resp.status_code == 422

print("\nPASS: full chain works end-to-end (FastAPI -> Module 1/2/3 -> KG persist+retrieve).")
