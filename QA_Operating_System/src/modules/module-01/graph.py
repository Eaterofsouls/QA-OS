from typing import TypedDict


class Module01State(TypedDict, total=False):
    """LangGraph state shape for Module 1's workflow.

    TODO: this is a minimal placeholder, just enough for `import module_01`
    to succeed (it was previously missing entirely, which broke that import
    for every consumer). build_module01_graph() below remains an honest
    no-op -- real LangGraph orchestration is out of scope for this pass; the
    vertical slice calls RequirementRiskAssessor.assess() directly instead.
    """
    requirement_id: str
    tenant_id: str
    requirement_text: str
    source_tool: str
    risk_assessment: dict


def build_module01_graph():
    # TODO: not implemented -- see Module01State docstring above.
    pass