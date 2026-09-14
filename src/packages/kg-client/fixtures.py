"""
KG Client Fixtures — Sample data for stub implementation.
==========================================================

These fixtures are used when the in-memory stub has no data for a tenant.
They provide realistic sample data covering requirements, test cases,
and their relationships — matching the QA OS domain model.

These are NEVER used by the real Neo4j client.
"""

import datetime

# ---------------------------------------------------------------------------
# Sample generic nodes
# ---------------------------------------------------------------------------

FIXTURE_NODES: list[dict] = [
    {
        "id": "node-001",
        "label": "Component",
        "name": "Authentication Service",
        "description": "Handles user authentication and session management",
        "tenant_id": "fixture-tenant",
        "created_at": datetime.datetime(2024, 1, 10, 9, 0, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 10, 9, 0, 0).isoformat(),
    },
    {
        "id": "node-002",
        "label": "Component",
        "name": "Data Ingestion Pipeline",
        "description": "Ingests and normalises raw requirement documents",
        "tenant_id": "fixture-tenant",
        "created_at": datetime.datetime(2024, 1, 10, 9, 5, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 10, 9, 5, 0).isoformat(),
    },
    {
        "id": "node-003",
        "label": "Component",
        "name": "Report Generator",
        "description": "Generates traceability and compliance reports",
        "tenant_id": "fixture-tenant",
        "created_at": datetime.datetime(2024, 1, 10, 9, 10, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 10, 9, 10, 0).isoformat(),
    },
]

# ---------------------------------------------------------------------------
# Sample Requirement nodes (Module 1 domain)
# ---------------------------------------------------------------------------

FIXTURE_REQUIREMENTS: list[dict] = [
    {
        "id": "req-001",
        "label": "Requirement",
        "title": "User Authentication",
        "description": (
            "The system SHALL authenticate users via OAuth2/OIDC before granting access "
            "to any protected resource. MFA shall be enforced for admin roles."
        ),
        "priority": "MUST",
        "source_document": "SRS-v1.2.pdf",
        "source_section": "4.1.1",
        "status": "approved",
        "tenant_id": "fixture-tenant",
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
        "created_at": datetime.datetime(2024, 1, 15, 10, 0, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 15, 10, 0, 0).isoformat(),
    },
    {
        "id": "req-002",
        "label": "Requirement",
        "title": "Data Encryption at Rest",
        "description": (
            "All data at rest SHALL be encrypted using AES-256. Encryption keys "
            "MUST be managed by a dedicated KMS and rotated every 90 days."
        ),
        "priority": "MUST",
        "source_document": "SRS-v1.2.pdf",
        "source_section": "4.2.3",
        "status": "approved",
        "tenant_id": "fixture-tenant",
        "embedding": [0.2, 0.3, 0.4, 0.5, 0.6],
        "created_at": datetime.datetime(2024, 1, 15, 10, 15, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 15, 10, 15, 0).isoformat(),
    },
    {
        "id": "req-003",
        "label": "Requirement",
        "title": "API Response Time SLA",
        "description": (
            "95th-percentile API response time SHALL remain below 200ms under normal load. "
            "Degraded responses SHALL return within 1000ms with a 503 status."
        ),
        "priority": "SHOULD",
        "source_document": "NFR-v1.0.pdf",
        "source_section": "3.1",
        "status": "draft",
        "tenant_id": "fixture-tenant",
        "embedding": [0.3, 0.4, 0.5, 0.6, 0.7],
        "created_at": datetime.datetime(2024, 1, 16, 8, 30, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 16, 8, 30, 0).isoformat(),
    },
    {
        "id": "req-004",
        "label": "Requirement",
        "title": "Audit Logging",
        "description": (
            "All privileged actions SHALL be recorded in an immutable audit log. "
            "Logs SHALL include actor ID, timestamp, action, and affected resource."
        ),
        "priority": "MUST",
        "source_document": "SRS-v1.2.pdf",
        "source_section": "4.5.1",
        "status": "approved",
        "tenant_id": "fixture-tenant",
        "embedding": [0.4, 0.5, 0.6, 0.7, 0.8],
        "created_at": datetime.datetime(2024, 1, 16, 9, 0, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 16, 9, 0, 0).isoformat(),
    },
]

# ---------------------------------------------------------------------------
# Sample TestCase nodes (Module 6 domain)
# ---------------------------------------------------------------------------

FIXTURE_TEST_CASES: list[dict] = [
    {
        "id": "tc-001",
        "label": "TestCase",
        "title": "OAuth2 Login Success",
        "description": "Verify that a valid user can log in via OAuth2 and receive a JWT token.",
        "type": "functional",
        "covers_requirement": "req-001",
        "steps": [
            "Navigate to /auth/login",
            "Submit valid OAuth2 credentials",
            "Assert HTTP 200 with JWT in response body",
            "Assert JWT contains correct user claims",
        ],
        "expected_result": "JWT token returned, user session created",
        "status": "active",
        "tenant_id": "fixture-tenant",
        "created_at": datetime.datetime(2024, 1, 20, 14, 0, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 20, 14, 0, 0).isoformat(),
    },
    {
        "id": "tc-002",
        "label": "TestCase",
        "title": "Encryption Verification at Rest",
        "description": "Verify that stored objects are encrypted with AES-256.",
        "type": "security",
        "covers_requirement": "req-002",
        "steps": [
            "Write test record to database",
            "Inspect raw storage via DBA credentials",
            "Assert stored bytes are not plaintext",
            "Verify encryption algorithm metadata",
        ],
        "expected_result": "Data is unreadable without decryption key",
        "status": "active",
        "tenant_id": "fixture-tenant",
        "created_at": datetime.datetime(2024, 1, 20, 14, 30, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 20, 14, 30, 0).isoformat(),
    },
    {
        "id": "tc-003",
        "label": "TestCase",
        "title": "API p95 Latency Under Load",
        "description": "Verify API p95 latency stays below 200ms at 500 RPS.",
        "type": "performance",
        "covers_requirement": "req-003",
        "steps": [
            "Run k6 load script at 500 RPS for 5 minutes",
            "Collect p95 latency metric",
            "Assert p95 < 200ms",
        ],
        "expected_result": "p95 latency < 200ms",
        "status": "draft",
        "tenant_id": "fixture-tenant",
        "created_at": datetime.datetime(2024, 1, 21, 9, 0, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 21, 9, 0, 0).isoformat(),
    },
    {
        "id": "tc-004",
        "label": "TestCase",
        "title": "Audit Log Immutability",
        "description": "Attempt to delete an audit log entry and assert failure.",
        "type": "security",
        "covers_requirement": "req-004",
        "steps": [
            "Perform privileged action as admin user",
            "Locate resulting audit log entry",
            "Attempt DELETE on audit log record",
            "Assert 403 Forbidden or equivalent",
        ],
        "expected_result": "Audit log entries cannot be deleted",
        "status": "active",
        "tenant_id": "fixture-tenant",
        "created_at": datetime.datetime(2024, 1, 21, 10, 0, 0).isoformat(),
        "updated_at": datetime.datetime(2024, 1, 21, 10, 0, 0).isoformat(),
    },
]

# ---------------------------------------------------------------------------
# Sample relationships between nodes
# ---------------------------------------------------------------------------

FIXTURE_RELATIONSHIPS: list[dict] = [
    {
        "id": "rel-001",
        "from_id": "tc-001",
        "to_id": "req-001",
        "rel_type": "COVERS",
        "properties": {"confidence": 0.95},
    },
    {
        "id": "rel-002",
        "from_id": "tc-002",
        "to_id": "req-002",
        "rel_type": "COVERS",
        "properties": {"confidence": 0.92},
    },
    {
        "id": "rel-003",
        "from_id": "tc-003",
        "to_id": "req-003",
        "rel_type": "COVERS",
        "properties": {"confidence": 0.88},
    },
    {
        "id": "rel-004",
        "from_id": "tc-004",
        "to_id": "req-004",
        "rel_type": "COVERS",
        "properties": {"confidence": 0.97},
    },
    {
        "id": "rel-005",
        "from_id": "req-001",
        "to_id": "req-004",
        "rel_type": "RELATED_TO",
        "properties": {"reason": "Auth actions must be audited"},
    },
]
