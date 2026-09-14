"""
Standalone verification for Step 6 (retrieval-based memory / retrieval-
augmented prompting for Module 1).

Run from services/api/ with: uv run python3 verify_step6_retrieval_memory.py

Same approach as verify_step3.py/verify_step4_module3.py/verify_step5_cost_
ledger.py: monkeypatches main.get_extraction_backbone so the LLM call is a
fake in this environment (no API key / LiteLLM instance reachable) --
everything else (FastAPI routing, RequirementRiskAssessor's real prompt
construction, KGClientStub.find_similar_requirements()'s real TF-IDF cosine
similarity, real KG persistence/retrieval, Module 3's real review
persistence) is genuine, unmocked production code.

Unlike the earlier scripts, the FakeLLM here also RECORDS every prompt it
was sent, so this script can show -- not just claim -- that the second
assessment's constructed prompt genuinely included the first requirement's
real stored outcome (risk level + human review decision) as few-shot
context. This is the concrete before/after proof requested: same shape of
requirement assessed twice, second prompt provably different from the
first because of what's now stored in the KG.
"""
import uuid

import main as main_module
from extraction import ExtractionBackbone
from fastapi.testclient import TestClient

# --- Canned LLM responses -------------------------------------------------
# Four calls happen in this script, in order: assess #1, generate-tests #1,
# assess #2, generate-tests #2. RISK_JSON_1/2 and TESTS_JSON_1/2 are handed
# out in that order below.
RISK_JSON_1 = (
    '{"requirement_id": "placeholder", "risk_score": 0.82, "risk_level": "high", '
    '"risk_rationale": "Auth/session changes affect all users", '
    '"risk_factors": ["auth", "external-facing"], "confidence": 0.9, "citation_ids": []}'
)
TESTS_JSON_1 = (
    '{"requirement_id": "placeholder", "test_cases": ['
    '{"title": "Reject invalid token", "description": "d", "steps": ["s1"], '
    '"expected_result": "401", "test_type": "negative", "priority": "high"}], '
    '"generation_confidence": 0.85}'
)
RISK_JSON_2 = (
    '{"requirement_id": "placeholder", "risk_score": 0.6, "risk_level": "medium", '
    '"risk_rationale": "Similar auth surface, narrower change", '
    '"risk_factors": ["auth"], "confidence": 0.8, "citation_ids": []}'
)
TESTS_JSON_2 = (
    '{"requirement_id": "placeholder", "test_cases": ['
    '{"title": "Session survives token refresh", "description": "d", "steps": ["s1"], '
    '"expected_result": "session intact", "test_type": "positive", "priority": "medium"}], '
    '"generation_confidence": 0.8}'
)
_RESPONSE_SEQUENCE = [RISK_JSON_1, TESTS_JSON_1, RISK_JSON_2, TESTS_JSON_2]

captured_prompts: list[str] = []


class RecordingFakeLLM:
    """Same fake-network-boundary shape as verify_step3.py's FakeLLM, plus
    recording of the actual `messages` it was sent so this script can show
    the real constructed prompt, not just the final parsed output.
    """
    def __init__(self, content: str):
        self._content = content

    async def complete(self, model, messages, **kwargs):
        # messages[-1] is the user message -- the actual prompt string
        # RequirementRiskAssessor.assess() built, including (or not) the
        # few-shot retrieval block. messages[0] is the schema system prompt
        # (see extraction/backbone.py), unrelated to retrieval.
        captured_prompts.append(messages[-1]["content"])
        return {"choices": [{"message": {"content": self._content}}]}


def fake_get_extraction_backbone(tenant_id: str) -> ExtractionBackbone:
    idx = fake_get_extraction_backbone.calls
    fake_get_extraction_backbone.calls += 1
    return ExtractionBackbone(llm_client=RecordingFakeLLM(_RESPONSE_SEQUENCE[idx]))


fake_get_extraction_backbone.calls = 0
main_module.get_extraction_backbone = fake_get_extraction_backbone

client = TestClient(main_module.app)
tenant_id = str(uuid.uuid4())

# --- Requirement #1: nothing stored yet for this tenant -------------------
req1_id = "req-retrieval-001"
req1_text = (
    "Users must be able to log in via OAuth2, including token refresh and "
    "session expiry handling."
)

resp = client.post(
    f"/requirements/{req1_id}/assess",
    json={"tenant_id": tenant_id, "requirement_text": req1_text, "source_tool": "manual"},
)
print("POST /assess (req #1) ->", resp.status_code)
assert resp.status_code == 200
risk1 = resp.json()
assert risk1["risk_level"] == "high"

# Nothing to retrieve yet -- this must be an honest empty list, not a
# fabricated match, and nothing should have been injected into the prompt.
assert risk1["retrieval"]["similar_requirements"] == [], (
    f"expected no matches for the first-ever requirement, got {risk1['retrieval']}"
)
first_prompt = captured_prompts[-1]
assert "Similar past requirement" not in first_prompt, (
    "retrieval block leaked into the prompt with nothing real to inject"
)
print("  retrieval.similar_requirements == [] (correct -- nothing stored yet)")

# Generate + approve req #1's test case, so req #1 has a real stored risk
# assessment AND a real stored human review decision by the time req #2 is
# assessed below.
resp = client.post(f"/requirements/{req1_id}/generate-tests", json={"tenant_id": tenant_id})
assert resp.status_code == 200

resp = client.get(f"/requirements/{req1_id}/tests", params={"tenant_id": tenant_id})
assert resp.status_code == 200
tc1_id = resp.json()["test_cases"][0]["id"]

resp = client.post(
    f"/requirements/{req1_id}/tests/{tc1_id}/review",
    json={"tenant_id": tenant_id, "reviewer_id": "qa-lead-jane", "decision": "approved", "note": "Looks solid."},
)
print("POST /review (req #1's test case, approved) ->", resp.status_code)
assert resp.status_code == 200

# --- Requirement #2: a close paraphrase of #1, same tenant -----------------
req2_id = "req-retrieval-002"
req2_text = (
    "Users must be able to log in using OAuth2, including refreshing tokens "
    "and handling session expiry."
)

resp = client.post(
    f"/requirements/{req2_id}/assess",
    json={"tenant_id": tenant_id, "requirement_text": req2_text, "source_tool": "manual"},
)
print("POST /assess (req #2) ->", resp.status_code)
assert resp.status_code == 200
risk2 = resp.json()

matches = risk2["retrieval"]["similar_requirements"]
print(f"  retrieval.similar_requirements: {matches}")
assert len(matches) == 1, f"expected req #1 to be retrieved as a match, got {matches}"
match = matches[0]
assert match["requirement_id"] == req1_id
assert match["requirement_text"] == req1_text
assert match["risk_level"] == "high"          # req #1's REAL stored risk level
assert match["review_decision"] == "approved"  # req #1's REAL stored human decision
assert match["similarity"] >= risk2["retrieval"]["similarity_threshold"]

second_prompt = captured_prompts[-1]

print("\n" + "=" * 78)
print("ACTUAL CONSTRUCTED PROMPT SENT TO THE LLM FOR REQUIREMENT #2")
print("(this is messages[-1]['content'] as built by")
print(" modules/module-01/assessor.py's RequirementRiskAssessor.assess() --")
print(" not the final output, the real prompt text itself)")
print("=" * 78)
print(second_prompt)
print("=" * 78 + "\n")

assert "Similar past requirement" in second_prompt
assert req1_text in second_prompt, "req #1's actual text should appear verbatim in the few-shot block"
assert "risk_level high" in second_prompt
assert "approved by a human reviewer" in second_prompt

print("BEFORE (req #1's prompt) contained no retrieval block:")
print(f"  'Similar past requirement' in first_prompt  -> {'Similar past requirement' in first_prompt}")
print("AFTER (req #2's prompt) genuinely includes req #1's real stored outcome:")
print(f"  'Similar past requirement' in second_prompt -> {'Similar past requirement' in second_prompt}")
print(f"  req #1's risk_level ('high') present        -> {'risk_level high' in second_prompt}")
print(f"  req #1's review decision ('approved') present -> {'approved by a human reviewer' in second_prompt}")

print(
    "\nPASS: retrieval-based memory is real and non-cosmetic -- the second "
    "assessment's actual constructed prompt provably differs from the "
    "first because of what got stored in the KG in between, via TF-IDF "
    "cosine similarity (packages/kg-client/similarity.py) over real "
    "requirement text, not model fine-tuning/retraining."
)
