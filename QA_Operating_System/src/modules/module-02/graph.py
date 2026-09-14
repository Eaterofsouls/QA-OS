from typing import TypedDict


class Module02State(TypedDict, total=False):
    """LangGraph state shape for Module 2's workflow.

    TODO: minimal placeholder, same situation as Module01State in
    module-01/graph.py -- just enough for `import module_02` to succeed.
    build_module02_graph() remains an honest no-op; the vertical slice calls
    TestSuiteGenerator.generate() directly instead of a LangGraph workflow.
    """
    requirement_id: str
    tenant_id: str
    risk_assessment: dict
    generated_tests: list


def build_module02_graph():
    # TODO: not implemented -- see Module02State docstring above.
    pass