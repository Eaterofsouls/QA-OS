import json
import logging
from pydantic import BaseModel, ValidationError
from typing import TypeVar, Type

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when the LLM's response can't be turned into a valid output_type.

    Previously, any failure here (malformed JSON, a response that doesn't
    match the schema, a missing field) was swallowed and replaced with
    `output_type.construct()` -- an UNVALIDATED, mostly-empty pydantic object
    built without calling __init__, silently masquerading as a real result.
    Callers -- and anyone eyeballing the API response -- had no way to tell a
    real assessment from an empty shell. This now raises instead, with the
    raw LLM content attached so the failure is visible and debuggable.
    """
    def __init__(self, message: str, *, raw_content: str, cause: Exception | None = None):
        super().__init__(message)
        self.raw_content = raw_content
        self.__cause__ = cause


class ExtractionBackbone:
    def __init__(self, llm_client, cost_ledger=None):
        self.llm = llm_client
        # Resolved lazily to get_cost_ledger() in extract() if not given --
        # keeps this constructor's signature backward compatible with every
        # existing caller (get_extraction_backbone(), the verify_step*.py
        # scripts) that only ever passed llm_client positionally/by keyword.
        self.cost_ledger = cost_ledger

    async def extract(
        self,
        prompt: str,
        output_type: Type[T],
        model: str = "gpt-4o",
        requirement_id: str | None = None,
    ) -> T:
        messages = [
            {"role": "system", "content": f"Output JSON matching this schema: {output_type.model_json_schema()}"},
            {"role": "user", "content": prompt}
        ]
        res = await self.llm.complete(model, messages, response_format={"type": "json_object"})

        # Real cost/usage capture -- logged for every real call that made it
        # this far, regardless of what happens to the response content below.
        # A call that returned malformed JSON or a schema mismatch still
        # consumed real tokens; only a call that never got a response at all
        # (LLMGatewayError, raised inside self.llm.complete() before we get
        # here) produces no ledger entry, because there's nothing real to log.
        self._log_cost(res, model=model, requirement_id=requirement_id)

        content = res.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ExtractionError(
                f"LLM response was not valid JSON: {exc}", raw_content=content, cause=exc
            ) from exc
        try:
            return output_type(**data)
        except ValidationError as exc:
            raise ExtractionError(
                f"LLM response JSON didn't match {output_type.__name__}'s schema: {exc}",
                raw_content=content,
                cause=exc,
            ) from exc

    def _log_cost(self, response: dict, *, model: str, requirement_id: str | None) -> None:
        """Record the real usage from `response` to the CostLedger.

        Deliberately isolated in its own try/except: a failure writing to
        the cost ledger (e.g. a disk/permissions problem) must never break
        an otherwise-successful /assess or /generate-tests call -- that
        would make a side-channel audit log more load-bearing than the
        actual product response. This is different from the swallowed
        LLMGatewayError/ExtractionError failures this module previously had
        (see class docstrings above): those hid a *failed* call behind a
        fake *successful* one. This only isolates a logging side-effect
        from a call whose real outcome (success or failure) is unaffected
        either way.
        """
        from llm_gateway_client.client import extract_usage
        from llm_gateway_client.ledger import get_cost_ledger

        try:
            usage = extract_usage(response)
            ledger = self.cost_ledger or get_cost_ledger()
            tenant_id = getattr(self.llm, "tenant_id", None) or "unknown"
            ledger.record_call(
                tenant_id=tenant_id,
                model=model,
                requirement_id=requirement_id,
                usage=usage,
            )
        except Exception:
            logger.exception("CostLedger.record_call failed; continuing without a cost entry")


def get_extraction_backbone(tenant_id: str) -> "ExtractionBackbone":
    """Config-driven factory: wires a real LLMGatewayClient (reads
    LITELLM_BASE_URL / LITELLM_API_KEY from the environment) into a fresh
    ExtractionBackbone. This is the piece that was previously missing
    entirely -- nothing instantiated a real client anywhere.

    Also wires the real CostLedger (get_cost_ledger()) via
    ExtractionBackbone's default -- every real call made through the
    backbone this factory produces gets a real logged entry.
    """
    from llm_gateway_client import get_llm_client

    return ExtractionBackbone(llm_client=get_llm_client(tenant_id))
