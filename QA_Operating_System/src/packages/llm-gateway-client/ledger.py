"""Real cost-ledger persistence for LLM calls made through this gateway.

Previously: `class CostLedger: pass` -- no storage, no schema, nothing.

STORAGE CHOICE: SQLite (stdlib `sqlite3`), not in-memory.
Why: a cost/billing record that vanishes the moment the process restarts
defeats the point of tracking it at all -- unlike kg-client's in-memory
KGClientStub (explicitly a throwaway Sprint-0 stand-in that's fine to lose
on restart, see kg_client/stub.py), a cost ledger is meant to be an audit
trail someone can point to later ("what did that call actually cost").
SQLite needs no new dependency (stdlib only) and no running infra (unlike
the real Postgres/Neo4j this repo already has, both out of scope here),
while still giving real persistence and real filtered queries (WHERE
tenant_id = ? AND requirement_id = ?) for the GET /requirements/{id}/cost
endpoint added in services/api/main.py. Defaults to a file next to this
module; override the path with the LEDGER_DB_PATH env var (":memory:" is
a valid value, e.g. for tests that shouldn't touch disk).

EXPLICITLY NOT IMPLEMENTED HERE: CostCeiling enforcement (blocking/rejecting
a call because a tenant is over budget). That's cost_ceiling.py, deliberately
left as `class CostCeiling: pass` -- out of scope for this pass, per the
explicit instruction not to touch ceiling-triggered call rejection.
"""
import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Pricing table -- HARDCODED, APPROXIMATE, NOT A LIVE PRICING API.
#
# These are publicly published per-1K-token list prices, current as of this
# engineering pass (Aug 2026), used ONLY so that estimated_cost_usd has a
# stated, inspectable basis instead of being invented out of thin air. They
# WILL drift out of date -- if you're reading this later, check the
# provider's real pricing page before trusting estimated_cost_usd for
# anything that matters financially. This is an estimate for engineering
# visibility, not a billing-grade figure.
#
# Models not in this table price as "unknown" (None), never as a guess.
# ---------------------------------------------------------------------------
PRICING_USD_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o":                      {"prompt": 0.0025, "completion": 0.0100},
    "gpt-4o-mini":                 {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4-turbo":                 {"prompt": 0.0100, "completion": 0.0300},
    "gpt-4":                       {"prompt": 0.0300, "completion": 0.0600},
    "gpt-3.5-turbo":               {"prompt": 0.0005, "completion": 0.0015},
    "claude-3-5-sonnet-20241022":  {"prompt": 0.0030, "completion": 0.0150},
    "claude-3-5-haiku-20241022":   {"prompt": 0.0008, "completion": 0.0040},
    "claude-3-opus-20240229":      {"prompt": 0.0150, "completion": 0.0750},
}
PRICING_BASIS = (
    "Hardcoded approximate per-1K-token list prices as of the Aug 2026 "
    "engineering pass -- NOT fetched from a live pricing API. See "
    "PRICING_USD_PER_1K_TOKENS in packages/llm-gateway-client/ledger.py. "
    "Unrecognized models, or calls with unknown token counts, price as "
    "null/unknown rather than being guessed."
)


@dataclass
class LedgerEntry:
    id: str
    tenant_id: str
    requirement_id: Optional[str]
    model: str
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    usage_reported: bool  # True iff the provider's response actually included a "usage" object
    estimated_cost_usd: Optional[float]
    cost_basis: Optional[str]  # None whenever estimated_cost_usd is None -- there's nothing to explain
    timestamp: str  # ISO-8601 UTC

    def to_dict(self) -> dict:
        return asdict(self)


class CostLedger:
    """SQLite-backed ledger of real LLM call token/cost usage.

    One row per real call to LLMGatewayClient.complete() made through
    ExtractionBackbone.extract() (see extraction/backbone.py, which is the
    real call path wired into every /assess and /generate-tests request).
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv(
            "LEDGER_DB_PATH",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "cost_ledger.db"),
        )
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cost_ledger_entries (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    requirement_id TEXT,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    usage_reported INTEGER NOT NULL,
                    estimated_cost_usd REAL,
                    cost_basis TEXT,
                    timestamp TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def record_call(
        self,
        *,
        tenant_id: str,
        model: str,
        requirement_id: Optional[str] = None,
        usage: Optional[dict] = None,
    ) -> LedgerEntry:
        """Log one real LLM call.

        `usage` is exactly what llm_gateway_client.client.extract_usage()
        returned: None if the provider's response had no "usage" object at
        all (record that honestly as unknown/unreported), otherwise a dict
        whose individual fields may themselves be None if the provider
        omitted them.
        """
        usage_reported = usage is not None
        prompt_tokens = usage.get("prompt_tokens") if usage else None
        completion_tokens = usage.get("completion_tokens") if usage else None
        total_tokens = usage.get("total_tokens") if usage else None

        estimated_cost_usd: Optional[float] = None
        cost_basis: Optional[str] = None
        pricing = PRICING_USD_PER_1K_TOKENS.get(model)
        if pricing is not None and prompt_tokens is not None and completion_tokens is not None:
            estimated_cost_usd = round(
                (prompt_tokens / 1000.0) * pricing["prompt"]
                + (completion_tokens / 1000.0) * pricing["completion"],
                6,
            )
            cost_basis = PRICING_BASIS
        # else: model isn't in the hardcoded table, or we don't have real
        # token counts to multiply -- leave both None. Never fabricate.

        entry = LedgerEntry(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id or "unknown",
            requirement_id=requirement_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            usage_reported=usage_reported,
            estimated_cost_usd=estimated_cost_usd,
            cost_basis=cost_basis,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO cost_ledger_entries "
                "(id, tenant_id, requirement_id, model, prompt_tokens, completion_tokens, "
                " total_tokens, usage_reported, estimated_cost_usd, cost_basis, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entry.id, entry.tenant_id, entry.requirement_id, entry.model,
                    entry.prompt_tokens, entry.completion_tokens, entry.total_tokens,
                    int(entry.usage_reported), entry.estimated_cost_usd, entry.cost_basis,
                    entry.timestamp,
                ),
            )
            self._conn.commit()
        return entry

    def get_entries_for_requirement(self, tenant_id: str, requirement_id: str) -> list[LedgerEntry]:
        """Real logged entries for one tenant+requirement, oldest first --
        backs GET /requirements/{id}/cost. No estimation, no synthesis:
        this is a straight read of whatever record_call() actually wrote."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, tenant_id, requirement_id, model, prompt_tokens, completion_tokens, "
                "total_tokens, usage_reported, estimated_cost_usd, cost_basis, timestamp "
                "FROM cost_ledger_entries WHERE tenant_id = ? AND requirement_id = ? "
                "ORDER BY timestamp ASC",
                (tenant_id, requirement_id),
            )
            rows = cur.fetchall()
        return [
            LedgerEntry(
                id=r[0], tenant_id=r[1], requirement_id=r[2], model=r[3],
                prompt_tokens=r[4], completion_tokens=r[5], total_tokens=r[6],
                usage_reported=bool(r[7]), estimated_cost_usd=r[8], cost_basis=r[9],
                timestamp=r[10],
            )
            for r in rows
        ]


_default_ledger: Optional[CostLedger] = None
_default_ledger_lock = threading.Lock()


def get_cost_ledger() -> CostLedger:
    """Process-wide singleton factory, mirroring get_llm_client() /
    get_extraction_backbone()'s pattern elsewhere in this package. A single
    shared SQLite connection is fine here -- writes are short, and access is
    already serialized with a lock; this is a lightweight audit log, not a
    high-throughput datastore."""
    global _default_ledger
    with _default_ledger_lock:
        if _default_ledger is None:
            _default_ledger = CostLedger()
        return _default_ledger
