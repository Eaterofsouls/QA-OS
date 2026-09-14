"""
Module 1: Requirement Risk Assessor
=====================================

Public API for the Requirement Risk Assessor module.

Exports:
    RequirementRiskAssessor: The main assessor class. Before building its
        prompt, it pulls similar past requirements for the tenant (via
        KGClientInterface.find_similar_requirements(), TF-IDF cosine
        similarity -- see kg-client/similarity.py) and injects their real
        stored risk assessment + human review decision as few-shot
        context. Retrieval-based memory / retrieval-augmented prompting --
        NOT model fine-tuning or training. See README.md §6/§7/§8.
    RiskAssessmentInput: Input model for a single requirement.
    RiskAssessmentOutput: Output model containing the risk assessment.
    RetrievalContext / SimilarRequirementMatch: What retrieval-based memory
        actually retrieved and injected for a given assess() call --
        readable via RequirementRiskAssessor.last_retrieval_context after
        assess() returns.
    build_module01_graph: Factory to build the LangGraph workflow.

Usage::

    from module_01 import RequirementRiskAssessor, RiskAssessmentInput
    from kg_client import get_client
    from extraction import get_extraction_backbone
    from llm_gateway_client import get_llm_client
    from config_service import get_config_service

    assessor = RequirementRiskAssessor(
        kg_client=get_client(),
        llm_client=get_llm_client(),
        config_service=get_config_service(),
        extraction_backbone=get_extraction_backbone(),
    )
    result = await assessor.assess(input_data)
"""

from module_01.assessor import (
    RequirementRiskAssessor,
    RiskAssessmentInput,
    RiskAssessmentOutput,
    RetrievalContext,
    SimilarRequirementMatch,
    SIMILARITY_THRESHOLD,
)
from module_01.graph import Module01State, build_module01_graph

__all__ = [
    "RequirementRiskAssessor",
    "RiskAssessmentInput",
    "RiskAssessmentOutput",
    "RetrievalContext",
    "SimilarRequirementMatch",
    "SIMILARITY_THRESHOLD",
    "Module01State",
    "build_module01_graph",
]
