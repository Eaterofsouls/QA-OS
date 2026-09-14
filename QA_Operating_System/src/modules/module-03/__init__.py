"""
Module 3: Human Review Gate
============================

Public API exports for the Human Review Gate module.

This module provides the FIRST mandatory human-in-the-loop gate in the QA-OS
pipeline. The orchestrator BLOCKS here until a human approves or rejects the
generated test suite. No AI decision-making occurs at this gate.

Usage::

    from module_03 import HumanReviewGate, ReviewRequest, ReviewDecision

    gate = HumanReviewGate(kg_client=client)
    req = await gate.create_review_request(
        tenant_id="tenant-abc",
        requirement_id="REQ-001",
        test_case_ids=["TC-1", "TC-2"],
        risk_context="High-risk authentication flow",
    )
    decision = await gate.wait_for_decision(req.id, timeout_seconds=3600)
"""

from module_03.gate import HumanReviewGate, ReviewDecision, ReviewRequest

__all__ = [
    "HumanReviewGate",
    "ReviewRequest",
    "ReviewDecision",
]
