import os
import httpx


class LLMGatewayError(Exception):
    """Raised when the LiteLLM gateway call fails (unreachable, timeout, non-2xx).

    Previously, this class swallowed every failure here and returned a fake
    "successful" empty completion (`{"choices": [{"message": {"content": "{}"}}]}`).
    That meant a misconfigured API key, an unreachable gateway, or a genuine
    provider error all looked identical to a real (if empty) LLM response --
    silently defeating the point of a "no fakes, no hardcoded output" prototype.
    Callers now get a real exception with the underlying cause attached.
    """
    def __init__(self, message: str, *, cause: Exception | None = None):
        super().__init__(message)
        self.__cause__ = cause


class LLMGatewayClient:
    """The ONLY permitted path to any LLM provider."""
    def __init__(self, tenant_id: str):
        self.base_url = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
        self.api_key = os.getenv("LITELLM_API_KEY", "sk-litellm-dev-key")
        self.tenant_id = tenant_id

    async def complete(self, model: str, messages: list[dict], max_tokens: int = 2048, **kwargs) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": model, "messages": messages, "max_tokens": max_tokens, **kwargs},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                raise LLMGatewayError(
                    f"LiteLLM gateway at {self.base_url} returned "
                    f"{exc.response.status_code}: {exc.response.text[:500]}",
                    cause=exc,
                ) from exc
            except httpx.HTTPError as exc:
                raise LLMGatewayError(
                    f"Could not reach LiteLLM gateway at {self.base_url} "
                    f"({type(exc).__name__}: {exc}). Is LITELLM_BASE_URL set and "
                    f"is the gateway running (see docker-compose.yml)?",
                    cause=exc,
                ) from exc

    async def embed(self, model: str, input_text: str | list[str]) -> list[list[float]]:
        # TODO(llm-gateway-client): still a hardcoded stub. Not on the critical
        # path for this pass (vector_search/hybrid_search are documented no-ops
        # in kg-client for the same reason) -- left untouched, flagged here for
        # honesty rather than silently claiming it embeds anything.
        return [[0.0] * 1536]


def extract_usage(response: dict) -> dict | None:
    """Pull real token usage out of an OpenAI-compatible chat-completion
    response, honestly -- no estimating, no defaulting missing data to 0.

    OpenAI-compatible APIs (direct OpenAI, LiteLLM gateway, most others)
    return a top-level "usage" object shaped like:
        {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    but it is NOT guaranteed to be present (some providers/proxies omit it
    entirely, e.g. on certain streaming or error-adjacent responses).

    Returns:
        None if the response has no "usage" object at all -- callers
        (see extraction/backbone.py, llm_gateway_client/ledger.py) must
        record that as "unknown", not silently treat it as zero tokens.
        Otherwise, a dict with prompt_tokens/completion_tokens/total_tokens,
        where any individual field the provider omitted is None rather than
        a fabricated number.
    """
    usage = response.get("usage")
    if not isinstance(usage, dict):
        return None
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def get_llm_client(tenant_id: str) -> LLMGatewayClient:
    """Config-driven factory. Reads LITELLM_BASE_URL / LITELLM_API_KEY from the
    environment (see LLMGatewayClient.__init__); this is just the one place
    callers should construct a client from, instead of instantiating it inline
    ad hoc in every module.
    """
    return LLMGatewayClient(tenant_id=tenant_id)
