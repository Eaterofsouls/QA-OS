"""
Module 2: Test Suite Generator
================================

Public API for the Test Suite Generator module.

Exports:
    TestSuiteGenerator: The main generator class.
    TestGenerationInput: Input model (wraps Module 1 output + requirement text).
    TestGenerationOutput: Output model containing generated test cases.
    GeneratedTestCase: Individual test case model.
    build_module02_graph: Factory to build the LangGraph workflow.

Usage::

    from module_02 import TestSuiteGenerator, TestGenerationInput
    from module_01 import RiskAssessmentOutput

    generator = TestSuiteGenerator(
        kg_client=get_client(),
        llm_client=get_llm_client(),
        config_service=get_config_service(),
        extraction_backbone=get_extraction_backbone(),
    )
    result = await generator.generate(input_data)

Note:
    Generated tests are stored as DRAFT status and require Module 3 human
    review/approval before they can be executed. This is by design — the
    AI-generated mutation score ceiling for V1 is documented at ~30-41%.
"""

from module_02.generator import (
    GeneratedTestCase,
    TestGenerationInput,
    TestGenerationOutput,
    TestSuiteGenerator,
)
from module_02.graph import Module02State, build_module02_graph

__all__ = [
    "TestSuiteGenerator",
    "TestGenerationInput",
    "TestGenerationOutput",
    "GeneratedTestCase",
    "Module02State",
    "build_module02_graph",
]
