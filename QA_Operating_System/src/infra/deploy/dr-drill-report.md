# DR Drill Report

**Document ID:** PACK-01 / Prompt_0104  
**Policy Reference:** [`backup-dr-policy.md`](./backup-dr-policy.md)  
**Report Version:** 1.0 (Completed Example — Synthetic Data)

---

## Drill Metadata

| Field | Value |
|-------|-------|
| **Drill Date** | 2026-06-15 |
| **Drill Type** | Unannounced (simulated page, no advance notice to on-call) |
| **Systems Under Test** | Neo4j Graph Substrate + MinIO Object Storage (`qa-os-traces`) |
| **Environment** | Staging (`qa-os-staging` cluster) |
| **Drill Lead** | Alex Rivera (Platform Team) |
| **Participants** | Alex Rivera, Morgan Chen (Graph Sub-lead), Jamie Okonkwo (SRE) |
| **Observers** | Engineering Director (Priya Kapoor) |
| **Total Duration** | 4 hours 22 minutes |

---

## Pre-Drill State

| System | Node Count | Object Count | Last Backup Age |
|--------|-----------|--------------|----------------|
| Neo4j (staging) | 14,872 nodes, 38,441 rels | — | 18 hours |
| MinIO `qa-os-traces` (staging) | — | 1,204 objects (47 GB) | 55 minutes |

---

## Deliberate Corruption Method

### Step 1 — Neo4j Corruption (10:02 UTC)

```cypher
-- Simulated accidental schema-breaking delete
-- Executed by drill lead on staging Cypher shell
MATCH (e:Entity) WHERE e.uuid STARTS WITH 'e-drill-'
DELETE e;
-- Result: 3,411 nodes deleted
-- THEN: Manually corrupted store files on disk to simulate hardware failure
-- docker exec neo4j-staging bash -c "dd if=/dev/urandom of=/data/databases/neo4j/neostore bs=1M count=5"
```

**Observed effect:** Neo4j service crashed on next restart with `StorageException: Corrupt store file`.

### Step 2 — MinIO Object Loss (10:08 UTC)

```bash
# Simulated accidental bulk delete of last 2 hours of traces
mc rm --recursive --force \
  "minio-staging/qa-os-traces/traces/" \
  --older-than 2h --newer-than 0h
# Result: 87 objects (3.2 GB) deleted
```

**Observed effect:** Application returned 404 for recent trace lookups; alert fired in Langfuse dashboard.

---

## Recovery Timeline

### Phase 1: Detection (10:08–10:14 UTC) — 6 min

| Time | Event |
|------|-------|
| 10:08 | Automated alert: `neo4j_down` fired in PagerDuty |
| 10:09 | Automated alert: `s3_error_rate_high` fired (404 rate > 5%) |
| 10:11 | On-call (Alex Rivera) acknowledges both alerts |
| 10:14 | Incident declared; Jamie Okonkwo joins bridge call |

### Phase 2: Neo4j Recovery (10:15–12:47 UTC) — 2 hr 32 min

| Time | Action | Duration |
|------|--------|----------|
| 10:15 | Stopped Neo4j container | 1 min |
| 10:16 | Identified last valid backup: `20260614` (18 hours old) | 3 min |
| 10:19 | Downloaded backup archive from MinIO cold path | 8 min |
| 10:27 | Ran `neo4j-admin database load` | 14 min |
| 10:41 | Started Neo4j; ran `connectivity_check.py` | 4 min |
| 10:45 | Spot-checked 10 random entities via cypher-shell | 7 min |
| 10:52 | Ran `pytest packages/ -k smoke` → 47/47 passed | 12 min |
| 11:04 | Declared Neo4j recovered | — |
| 11:04–12:47 | **Gap analysis:** 3,411 nodes from last 18 hours require replay from application logs | 103 min |
| 12:47 | Replay complete from audit log; entity count restored to 14,872 | — |

**Neo4j RTO (this drill):** 2 hr 32 min ✅ (target: ≤ 6 hr)  
**Neo4j RPO (this drill):** 18 hours ⚠️ (target: ≤ 24 hr — PASSED, but close)

### Phase 3: MinIO Recovery (10:15–10:57 UTC) — 42 min

| Time | Action | Duration |
|------|--------|----------|
| 10:15 | Identified missing objects via `mc ls` diff against hourly mirror | 6 min |
| 10:21 | Ran `mc mirror` from hourly mirror (55 min old) | 18 min |
| 10:39 | Verified object counts: 1,204/1,204 restored | 5 min |
| 10:44 | Ran `s3_setup.py` canary write/read | 3 min |
| 10:47 | Cleared 404 alert | — |
| 10:57 | Declared MinIO recovered | — |

**MinIO RTO (this drill):** 42 min ✅ (target: ≤ 4 hr)  
**MinIO RPO (this drill):** 55 minutes ✅ (target: ≤ 1 hr — PASSED)

---

## Findings & Action Items

| # | Finding | Severity | Owner | Due |
|---|---------|----------|-------|-----|
| 1 | Neo4j RPO close to 24h limit (18h backup age at drill time) | Medium | Morgan Chen | 2026-07-01 |
| 2 | No automated Neo4j backup age alert (fired manually this drill) | Medium | Alex Rivera | 2026-07-15 |
| 3 | Replay from audit logs took 103 min — replay tooling needs automation | Medium | Jamie Okonkwo | 2026-08-01 |
| 4 | Runbook URL not pinned in PagerDuty alert — on-call had to search | Low | Alex Rivera | 2026-07-01 |

---

## Result: **PASSED** ✅

Both systems recovered within their stated RTO and RPO targets. The Neo4j RPO was satisfied but with limited headroom — action item #1 tightens the backup schedule.

| System | RTO Target | RTO Actual | RPO Target | RPO Actual | Result |
|--------|-----------|-----------|-----------|-----------|--------|
| Neo4j | ≤ 6 hr | 2 hr 32 min | ≤ 24 hr | 18 hr | ✅ PASSED |
| MinIO | ≤ 4 hr | 42 min | ≤ 1 hr | 55 min | ✅ PASSED |

---

## Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Drill Lead | Alex Rivera | _(signed)_ | 2026-06-15 |
| Graph Sub-lead | Morgan Chen | _(signed)_ | 2026-06-16 |
| Engineering Director | Priya Kapoor | _(signed)_ | 2026-06-17 |

---

## Next Drill

**Scheduled:** 2026-09-15 (quarterly cadence)  
**Planned scope:** Full cluster failure simulation (both Neo4j and MinIO simultaneously)
