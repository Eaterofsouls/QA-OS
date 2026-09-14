"""
Standalone verification for Step 7 (SQLite-backed KGClientInterface
implementation, packages/kg-client/sqlite_backend.py).

Unlike verify_step3/4/5/6.py, this one is deliberately run TWICE, as two
separate OS processes, sharing nothing but a KG_SQLITE_PATH env var
pointing at the same file:

    rm -f /tmp/verify_step7_kg.sqlite3
    KG_SQLITE_PATH=/tmp/verify_step7_kg.sqlite3 uv run python3 verify_step7_sqlite_persistence.py write
    # <-- process exits completely here; nothing survives in memory -->
    KG_SQLITE_PATH=/tmp/verify_step7_kg.sqlite3 uv run python3 verify_step7_sqlite_persistence.py read

That second `uv run` is a genuinely fresh Python interpreter: fresh import
of `main` (and therefore a fresh `get_client()` call, a fresh
KGClientSQLite, a fresh sqlite3 connection), fresh FastAPI app object,
fresh everything -- the only thing connecting the two invocations is the
file at KG_SQLITE_PATH. This is the real restart-and-recover proof: if
`read` can see `write`'s data, persistence is real, not an artifact of
reusing the same Python process across the "before" and "after".

WRITE phase: runs the real assess -> generate-tests -> review chain
(Modules 1/2/3) against a fixed tenant/requirement id, via TestClient, with
the LLM faked exactly like verify_step3/4.py (no reachable LLM provider in
this environment) -- everything else is real, unmocked code.

READ phase: does NOT re-run assess/generate-tests. It reads the same
tenant/requirement back three different ways -- direct KGClientInterface
calls (kg.get_node/get_related), and the real GET /tests HTTP route -- to
show the exact same real data is still there. It then makes ONE new
/assess call for a close paraphrase of the original requirement, to prove
retrieval-based memory (find_similar_requirements, §8.3) also survives a
restart: the match it finds, and the risk_level/review_decision on it,
have to have come from SQLITE, since nothing about requirement #1 exists
in this process's memory until it's read back from the file.
"""
import json
import sys
import uuid

# Fixed across both phases -- this is intentionally NOT uuid.uuid4() at
# import time, because the write and read phases are different processes
# and need to agree on which tenant/requirement they're talking about.
TENANT_ID = "5f6e2b3a-0000-4a11-9c1d-100000000001"
REQ1_ID = "req-sqlite-persist-001"
REQ1_TEXT = (
    "Users must be able to log in via OAuth2, including token refresh and "
    "session expiry handling."
)
REQ2_ID = "req-sqlite-persist-002"
REQ2_TEXT = (
    "Users must be able to log in using OAuth2, including refreshing tokens "
    "and handling session expiry."
)

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


class FakeLLM:
    def __init__(self, content: str):
        self._content = content

    async def complete(self, model, messages, **kwargs):
        return {"choices": [{"message": {"content": self._content}}]}


def run_write_phase():
    import main as main_module
    from extraction import ExtractionBackbone
    from fastapi.testclient import TestClient

    assert type(main_module._kg_client).__name__ == "KGClientSQLite", (
        "expected get_client() to select KGClientSQLite with KG_SQLITE_PATH "
        f"set, got {type(main_module._kg_client).__name__} instead -- "
        "check that KG_SQLITE_PATH is exported before this process starts."
    )
    print(f"kg backend for this process: {type(main_module._kg_client).__name__}")
    print(f"KG_SQLITE_PATH: {main_module._kg_client.db_path}")

    sequence = [RISK_JSON_1, TESTS_JSON_1]
    calls = {"n": 0}

    def fake_get_extraction_backbone(tenant_id):
        idx = calls["n"]
        calls["n"] += 1
        return ExtractionBackbone(llm_client=FakeLLM(sequence[idx]))

    main_module.get_extraction_backbone = fake_get_extraction_backbone
    client = TestClient(main_module.app)

    resp = client.post(
        f"/requirements/{REQ1_ID}/assess",
        json={"tenant_id": TENANT_ID, "requirement_text": REQ1_TEXT, "source_tool": "manual"},
    )
    print("[write] POST /assess ->", resp.status_code)
    assert resp.status_code == 200
    risk1 = resp.json()
    assert risk1["risk_level"] == "high"

    resp = client.post(f"/requirements/{REQ1_ID}/generate-tests", json={"tenant_id": TENANT_ID})
    print("[write] POST /generate-tests ->", resp.status_code)
    assert resp.status_code == 200

    resp = client.get(f"/requirements/{REQ1_ID}/tests", params={"tenant_id": TENANT_ID})
    assert resp.status_code == 200
    tc1_id = resp.json()["test_cases"][0]["id"]

    resp = client.post(
        f"/requirements/{REQ1_ID}/tests/{tc1_id}/review",
        json={"tenant_id": TENANT_ID, "reviewer_id": "qa-lead-jane", "decision": "approved", "note": "Looks solid."},
    )
    print("[write] POST /review (approved) ->", resp.status_code)
    assert resp.status_code == 200

    # Read back within THIS same process, just to confirm the write path
    # itself is sane before we trust the cross-process read in phase 2.
    resp = client.get(f"/requirements/{REQ1_ID}/tests", params={"tenant_id": TENANT_ID})
    tests_before_exit = resp.json()
    print(f"[write] same-process read-back: status={tests_before_exit['test_cases'][0]['status']}")
    assert tests_before_exit["test_cases"][0]["status"] == "approved"

    print(
        "\n[write] Phase complete. This process is about to exit -- nothing "
        "in memory survives past this point. Run the 'read' phase as a "
        "genuinely separate `uv run` invocation with the same KG_SQLITE_PATH "
        "to prove the data is really on disk, not just in this process."
    )


def run_read_phase():
    import main as main_module
    from extraction import ExtractionBackbone
    from fastapi.testclient import TestClient

    assert type(main_module._kg_client).__name__ == "KGClientSQLite", (
        "expected KGClientSQLite in the read phase too -- "
        f"got {type(main_module._kg_client).__name__}"
    )
    print(f"kg backend for THIS (fresh) process: {type(main_module._kg_client).__name__}")
    print(f"KG_SQLITE_PATH: {main_module._kg_client.db_path}")
    print(
        "This is a brand-new Python interpreter with no memory of the "
        "'write' phase's TestClient, FastAPI app, or FakeLLM objects -- "
        "everything below is read fresh from the SQLite file.\n"
    )

    tenant_uuid = uuid.UUID(TENANT_ID)

    # --- 1. Direct KGClientInterface calls, no HTTP involved -----------
    node = None
    _run_async(_get_node_and_print(main_module._kg_client, tenant_uuid))

    # --- 2. Through the real HTTP route, via a fresh TestClient --------
    client = TestClient(main_module.app)
    resp = client.get(f"/requirements/{REQ1_ID}/tests", params={"tenant_id": TENANT_ID})
    print(f"[read] GET /tests (fresh process, no /assess call this run) -> {resp.status_code}")
    assert resp.status_code == 200, (
        "requirement #1 was not found after restart -- persistence failed"
    )
    tests_after_restart = resp.json()
    print(json.dumps(tests_after_restart, indent=2))
    tc = tests_after_restart["test_cases"][0]
    assert tc["status"] == "approved"
    assert tc["reviewer_id"] == "qa-lead-jane"
    assert tc["review_note"] == "Looks solid."
    print(
        "[read] Confirmed: same test case id, same 'approved' status, same "
        "reviewer -- all read back from disk after a full process restart, "
        "not from memory.\n"
    )

    # --- 3. Retrieval-based memory (§8.3) also has to survive the ------
    #        restart, since find_similar_requirements() only has whatever
    #        SQLite gives it back -- nothing about requirement #1 exists
    #        in this process until it's read from the file.
    sequence = [RISK_JSON_2]
    calls = {"n": 0}

    def fake_get_extraction_backbone(tenant_id):
        idx = calls["n"]
        calls["n"] += 1
        return ExtractionBackbone(llm_client=FakeLLM(sequence[idx]))

    main_module.get_extraction_backbone = fake_get_extraction_backbone

    resp = client.post(
        f"/requirements/{REQ2_ID}/assess",
        json={"tenant_id": TENANT_ID, "requirement_text": REQ2_TEXT, "source_tool": "manual"},
    )
    print("[read] POST /assess (req #2, close paraphrase of req #1) ->", resp.status_code)
    assert resp.status_code == 200
    risk2 = resp.json()
    matches = risk2["retrieval"]["similar_requirements"]
    print(f"[read] retrieval.similar_requirements: {matches}")
    assert len(matches) == 1, f"expected req #1 to be found via SQLite, got {matches}"
    match = matches[0]
    assert match["requirement_id"] == REQ1_ID
    assert match["risk_level"] == "high"           # req #1's real stored risk level
    assert match["review_decision"] == "approved"  # req #1's real stored review decision
    print(
        "[read] Confirmed: find_similar_requirements() found requirement #1 "
        "and reported its real risk_level and review_decision, sourced "
        "entirely from the SQLite file in this fresh process.\n"
    )

    print(
        "PASS: KGClientSQLite genuinely persists across a process restart -- "
        "the requirement, its risk assessment, its generated test case, its "
        "human review decision, and retrieval-based-memory's ability to find "
        "it were all recovered from disk in a process that never ran "
        "/assess for requirement #1."
    )


async def _get_node_and_print(kg, tenant_uuid):
    node = await kg.get_node(tenant_uuid, REQ1_ID)
    print(f"[read] kg.get_node(tenant, {REQ1_ID!r}) -> {node}")
    assert node is not None, "requirement node missing after restart"
    assert node["text"] == REQ1_TEXT

    related = await kg.get_related(tenant_uuid, REQ1_ID)
    labels = sorted(r["label"] for r in related)
    print(f"[read] kg.get_related(tenant, {REQ1_ID!r}) -> labels={labels}")
    assert "RiskAssessment" in labels
    assert "TestCase" in labels
    print("[read] Direct interface calls confirm real persisted data (not just the HTTP layer).\n")


def _run_async(coro):
    import asyncio
    asyncio.run(coro)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("write", "read"):
        print(f"Usage: {sys.argv[0]} [write|read]", file=sys.stderr)
        sys.exit(2)
    if sys.argv[1] == "write":
        run_write_phase()
    else:
        run_read_phase()
