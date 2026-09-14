from uuid import UUID

class TenantScopeEnforcer:
    """ADR-011: Every query MUST pass through this enforcer."""
    def enforce(self, query: str, params: dict, tenant_id: UUID) -> tuple[str, dict]:
        # Simple injection of tenant_id into parameters
        params["tenant_id"] = str(tenant_id)
        # In a real AST parser, we would strictly inject WHERE n.tenant_id = $tenant_id
        return query, params
