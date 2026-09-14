"""
Standalone verification for the CostLedger / GET /requirements/{id}/cost feature.

Run from services/api/ with: uv run python3 verify_step5_cost_ledger.py

Same approach as verify_step3.py / verify_step4_module3.py: monkeypatches
main.get_extraction_backbone so the two LLM-backed routes (/assess,
/generate-tests) get a canned response instead of a real network call (no
LLM endpoint reachable in this environment). Unlike the earlier scripts,
the FakeLLM here also carries a `tenant_id` attribute and a real-shaped
"usage" object in its response -- exercising the actual capture path in
extraction/backbone.py (ExtractionBackbone.extract -> _log_cost ->
CostLedger.record_call) exactly as a real OpenAI-compatible provider
response would.

Everything downstream of the fake network boundary is real, untouched
production code: FastAPI routing, Pydantic validation, KGClientStub
persistence, and -- the subject of this script -- CostLedger's real SQLite
writes and the real GET /requirements/{id}/cost route reading them back.

A THIRD call, /assess on a second requirement, uses a FakeLLM response with
NO "usage" key at all, to prove the "unknown, not fabricated" path: the
resulting ledger entry must show usage_reported=false and
estimated_cost_usd=null, not a guessed number.
"""
import os

# Use an isolated on-disk DB for this run so it doesn't mix with any other
# ledger data on the machine, and so the file can be inspected after.
os.environ["LEDGER_DB_PATH"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "verify_step5_cost_ledger.db"
)
if os.path.exists(os.environ["LEDGER_DB_PATH"]):
    os.remove(os.environ["LEDGER_DB_PATH"])

import uuid  # noqa: E402

import main as main_module  # noqa: E402
from extraction import ExtractionBackbone  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

RISK_JSON = (
    '{"requirement_id": "placeholder", "risk_score": 0.82, "risk_level": "high", '
    '"risk_rationale": "Auth changes affect all users", '
    '"risk_factors": ["auth", "external-facing"], "confidence": 0.9, "citation_ids": []}'
)
TESTS_JSON = (
    '{"requirement_id": "placeholder", "test_cases": ['
    '{"title": "Reject invalid token", "description": "d", "steps": ["s1"], '
    '"expected_result": "401", "test_type": "negative", "priority": "high"}], '
    '"generation_confidence": 0.85}'
)
RISK_JSON_NO_USAGE = (
    '{"requirement_id": "placeholder", "risk_score": 0.4, "risk_level": "medium", '
    '"risk_rationale": "Minor UI copy change", '
    '"risk_factors": ["low-blast-radius"], "confidence": 0.7, "citation_ids": []}'
)


class FakeLLMWithUsage:
    """Stands in for the real network boundary (see verify_step3.py's
    FakeLLM) -- but shaped like a real OpenAI-compatible response,
    including a real "usage" object with real-looking token counts, and a
    `tenant_id` attribute (LLMGatewayClient always carries one; this fake
    mirrors that so extraction/backbone.py's tenant_id capture is exercised
    for real)."""

    def __init__(self, content: str, tenant_id: str, prompt_tokens: int, completion_tokens: int):
        self._content = content
        self.tenant_id = tenant_id
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens

    async def complete(self, model, messages, **kwargs):
        return {
            "choices": [{"message": {"content": self._content}}],
            "usage": {
                "prompt_tokens": self._prompt_tokens,
                "completion_tokens": self._completion_tokens,
                "total_tokens": self._prompt_tokens + self._completion_tokens,
            },
        }


class FakeLLMNoUsage:
    """A provider response with NO usage field at all -- some proxies omit
    it. Used to prove the ledger records "unknown", not a fabricated 0 or a
    guessed number."""

    def __init__(self, content: str, tenant_id: str):
        self._content = content
        self.tenant_id = tenant_id

    async def complete(self, model, messages, **kwargs):
        return {"choices": [{"message": {"content": self._content}}]}


tenant_id = str(uuid.uuid4())
requirement_id = "req-cost-ledger-001"
requirement_id_no_usage = "req-cost-ledger-002"

_calls = {"n": 0}


def fake_get_extraction_backbone(tid: str) -> ExtractionBackbone:
    _calls["n"] += 1
    if _calls["n"] == 1:
        # /assess for requirement 1 -- known model, real usage numbers.
        return ExtractionBackbone(
            llm_client=FakeLLMWithUsage(RISK_JSON, tid, prompt_tokens=612, completion_tokens=143)
        )
    elif _calls["n"] == 2:
        # /generate-tests for requirement 1 -- known model, real usage numbers.
        return ExtractionBackbone(
            llm_client=FakeLLMWithUsage(TESTS_JSON, tid, prompt_tokens=580, completion_tokens=210)
        )
    else:
        # /assess for requirement 2 -- no usage field at all.
        return ExtractionBackbone(llm_client=FakeLLMNoUsage(RISK_JSON_NO_USAGE, tid))


main_module.get_extraction_backbone = fake_get_extraction_backbone

client = TestClient(main_module.app)

# The model name the fakes are asked for is the default "gpt-4o" (extract()'s
# default model=), which IS in PRICING_USD_PER_1K_TOKENS -- so requirement 1's
# two calls should produce real, non-null estimated costs.

# 1. /assess for requirement 1 (real usage)
resp = client.post(
    f"/requirements/{requirement_id}/assess",
    json={"tenant_id": tenant_id, "requirement_text": "Users must log in via OAuth2.", "source_tool": "manual"},
)
print("POST /assess ->", resp.status_code)
assert resp.status_code == 200

# 2. /generate-tests for requirement 1 (real usage)
resp = client.post(f"/requirements/{requirement_id}/generate-tests", json={"tenant_id": tenant_id})
print("POST /generate-tests ->", resp.status_code)
assert resp.status_code == 200

# 3. GET /requirements/{id}/cost for requirement 1 -- expect 2 entries, both
# with real token counts and a real, non-null estimated cost.
resp = client.get(f"/requirements/{requirement_id}/cost", params={"tenant_id": tenant_id})
print("GET /cost (requirement 1) ->", resp.status_code, resp.json())
assert resp.status_code == 200
cost = resp.json()
assert len(cost["entries"]) == 2, f"expected 2 ledger entries, got {len(cost['entries'])}"

assess_entry = cost["entries"][0]
gen_entry = cost["entries"][1]

assert assess_entry["prompt_tokens"] == 612
assert assess_entry["completion_tokens"] == 143
assert assess_entry["total_tokens"] == 755
assert assess_entry["usage_reported"] is True
assert assess_entry["model"] == "gpt-4o"
assert assess_entry["estimated_cost_usd"] is not None, "gpt-4o is in the pricing table, cost must be real"
expected_assess_cost = round((612 / 1000.0) * 0.0025 + (143 / 1000.0) * 0.0100, 6)
assert abs(assess_entry["estimated_cost_usd"] - expected_assess_cost) < 1e-9, (
    f"cost math mismatch: {assess_entry['estimated_cost_usd']} vs {expected_assess_cost}"
)
assert assess_entry["cost_basis"] is not None and "hardcoded" in assess_entry["cost_basis"].lower()

assert gen_entry["prompt_tokens"] == 580
assert gen_entry["completion_tokens"] == 210
assert gen_entry["estimated_cost_usd"] is not None

# Aggregate totals: both entries have known tokens/cost, so totals must be
# real sums, not null.
assert cost["total_prompt_tokens"] == 612 + 580
assert cost["total_completion_tokens"] == 143 + 210
expected_total_cost = round(assess_entry["estimated_cost_usd"] + gen_entry["estimated_cost_usd"], 6)
assert abs(cost["total_estimated_cost_usd"] - expected_total_cost) < 1e-9

print(
    f"Consistency check: assess+generate = "
    f"{cost['total_prompt_tokens']} prompt tok, {cost['total_completion_tokens']} completion tok, "
    f"${cost['total_estimated_cost_usd']} estimated -- matches ledger entries exactly."
)

# 4. GET /requirements/{id}/cost for a requirement with NO entries yet ->
# empty list, null aggregates, 200 (not a 404 -- see route docstring).
resp = client.get(f"/requirements/req-never-called/cost", params={"tenant_id": tenant_id})
print("GET /cost (no entries) ->", resp.status_code, resp.json())
assert resp.status_code == 200
assert resp.json()["entries"] == []
assert resp.json()["total_prompt_tokens"] is None
assert resp.json()["total_estimated_cost_usd"] is None

# 5. /assess for requirement 2, where the fake provider response has NO
# usage field at all -- proves the "unknown, not fabricated" path.
resp = client.post(
    f"/requirements/{requirement_id_no_usage}/assess",
    json={"tenant_id": tenant_id, "requirement_text": "Change a button label.", "source_tool": "manual"},
)
print("POST /assess (no usage in provider response) ->", resp.status_code)
assert resp.status_code == 200

resp = client.get(f"/requirements/{requirement_id_no_usage}/cost", params={"tenant_id": tenant_id})
print("GET /cost (requirement 2, no usage) ->", resp.status_code, resp.json())
assert resp.status_code == 200
cost2 = resp.json()
assert len(cost2["entries"]) == 1
entry2 = cost2["entries"][0]
assert entry2["usage_reported"] is False, "provider response had no usage field -- must be recorded honestly"
assert entry2["prompt_tokens"] is None
assert entry2["completion_tokens"] is None
assert entry2["estimated_cost_usd"] is None, "no real token counts -- cost must be null, never guessed"
assert entry2["cost_basis"] is None
# Because one entry has an unknown cost, the aggregate must ALSO be null --
# never silently treated as "0 extra cost" from the unknown entry.
assert cost2["total_estimated_cost_usd"] is None

print(
    "PASS: CostLedger records real usage from a real-shaped provider response, "
    "computes cost from the stated hardcoded pricing table, GET /cost returns "
    "exactly what was logged, and a provider response with no usage field is "
    "recorded as unknown (not fabricated) end-to-end through the real HTTP route."
)
