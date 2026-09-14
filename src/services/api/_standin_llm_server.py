"""
Stand-in LLM gateway, used ONLY because no real LITELLM_API_KEY / provider
endpoint is reachable in this verification environment (see README.md
§4 / §9: "no real LLM API key has ever been made through this pipeline").

This is a REAL HTTP server (stdlib http.server) bound to localhost:9999,
serving the same POST /chat/completions shape a LiteLLM gateway or direct
OpenAI-compatible endpoint would. LLMGatewayClient.complete() in
packages/llm-gateway-client/client.py makes a REAL httpx call to it over
REAL HTTP -- nothing about the client, the extraction backbone, the cost
ledger, or the FastAPI routes is mocked. Only this one process, standing in
for a real LLM provider, is fake -- exactly the same boundary the existing
verify_step3.py / verify_step4_module3.py scripts stub, just done here as a
real server instead of a Python monkeypatch, so `curl` against real
`uvicorn` can be used for end-to-end verification.

Returns a *different* canned response depending on call count, alternating
risk-assessment JSON and test-generation JSON, each wrapped in a realistic
"usage" object with distinct, real-looking token counts -- so it's possible
to verify the numbers reported by GET /requirements/{id}/cost are the exact
same numbers this server reported, not recomputed or guessed anywhere in
between.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

RISK_JSON = (
    '{"requirement_id": "placeholder", "risk_score": 0.82, "risk_level": "high", '
    '"risk_rationale": "OAuth2 changes affect every authenticated user; token '
    'refresh and session-expiry edge cases are historically high-defect areas.", '
    '"risk_factors": ["auth", "external-facing", "session-management"], '
    '"confidence": 0.88, "citation_ids": []}'
)
TESTS_JSON = (
    '{"requirement_id": "placeholder", "test_cases": ['
    '{"title": "Reject expired refresh token", "description": "Attempt to refresh '
    'a session with an expired refresh token.", "steps": ["Authenticate and let '
    'the refresh token expire", "Call the refresh endpoint"], '
    '"expected_result": "401 Unauthorized, session terminated", '
    '"test_type": "negative", "priority": "high"}, '
    '{"title": "Session extends on valid refresh", "description": "Refresh an '
    'active session before expiry.", "steps": ["Authenticate", "Call refresh '
    'before token expiry"], "expected_result": "New access token issued, '
    'session extended", "test_type": "positive", "priority": "medium"}'
    '], "generation_confidence": 0.81}'
)

_call_count = {"n": 0}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)  # drain the request body (not inspected -- content doesn't affect the canned reply)

        _call_count["n"] += 1
        n = _call_count["n"]
        if n == 1:
            content, prompt_tokens, completion_tokens = RISK_JSON, 634, 158
        else:
            content, prompt_tokens, completion_tokens = TESTS_JSON, 701, 246

        body = {
            "id": f"chatcmpl-standin-{n}",
            "object": "chat.completion",
            "model": "gpt-4o",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
        payload = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass  # keep stdout clean for the verification transcript


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9999), Handler)
    print("Stand-in LLM gateway listening on http://127.0.0.1:9999")
    server.serve_forever()
