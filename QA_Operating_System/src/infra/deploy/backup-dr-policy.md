# Backup & Disaster Recovery Policy

**Document ID:** PACK-01 / Prompt_0103  
**Status:** ACTIVE — Closes **Major Risk #8** (Insufficient DR coverage) and **Underengineering #2** (No defined recovery procedures)  
**Effective Date:** 2026-07-11  
**Owner:** Platform Team (`platform-team@qa-os.internal`)  
**Review Cycle:** Quarterly

---

## Executive Summary

This policy defines backup schedules, Recovery Time Objectives (RTO), Recovery Point Objectives (RPO), and step-by-step recovery procedures for the two stateful subsystems of the AI QA Operating System:

1. **Object Storage** — MinIO / AWS S3 (`qa-os-traces` bucket)
2. **Neo4j Graph Substrate** — Enterprise LTS 5.26.x

> **Requirement:** Both subsystems must be individually recoverable within their stated RTO/RPO without access to the other.

---

## 1. Object Storage (MinIO / S3)

### 1.1 Backup Schedule

| Schedule | Method | Retention |
|----------|--------|-----------|
| **Continuous** | MinIO erasure coding (EC:4) across 4+ drives | N/A (inline) |
| **Hourly** | MinIO `mc mirror` to secondary MinIO cluster or S3 bucket | 48 hours |
| **Daily** | Full snapshot (`mc mirror --watch --overwrite`) | 30 days |
| **Weekly** | Verified archive to cold storage | 90 days |

For managed AWS S3: S3 Cross-Region Replication (CRR) replaces the hourly mirror.

### 1.2 RTO and RPO

| Metric | Target |
|--------|--------|
| **RPO** | ≤ 1 hour (hourly mirror) |
| **RTO** | ≤ 4 hours (mirror restore) |

### 1.3 Recovery Steps

#### Scenario A: Single-bucket data loss

```bash
# 1. Identify the backup source
BACKUP_SOURCE="s3://qa-os-traces-backup"   # or secondary MinIO alias
TARGET_BUCKET="qa-os-traces"

# 2. Stop all write traffic to the bucket (pause ingestion workers)
#    Notify platform-team@qa-os.internal before proceeding.

# 3. Restore from last hourly mirror
mc mirror \
  --preserve \
  --overwrite \
  "${BACKUP_SOURCE}" \
  "minio/${TARGET_BUCKET}"

# 4. Verify object count matches expected (within RPO window tolerance)
mc ls --recursive "minio/${TARGET_BUCKET}" | wc -l

# 5. Resume write traffic
#    Notify platform-team@qa-os.internal when complete.
```

#### Scenario B: Full MinIO cluster loss

```bash
# 1. Provision new MinIO cluster (use Helm chart / Terraform in infra/deploy/)
# 2. Restore from weekly cold archive to new cluster
# 3. Replay hourly mirrors up to the last available snapshot
# 4. Validate object count and spot-check 5 random objects
# 5. Update S3_ENDPOINT_URL in all service configs
# 6. Perform canary write/read via: uv run python infra/deploy/s3_setup.py
```

---

## 2. Neo4j Graph Substrate

### 2.1 Backup Schedule

| Schedule | Method | Retention |
|----------|--------|-----------|
| **Daily** | `neo4j-admin database dump` (online, non-disruptive) | 7 days |
| **Weekly** | Full offline dump + upload to S3 cold path | 30 days |
| **Before each schema migration** | Ad-hoc dump tagged with migration name | Until migration validated (min 7 days) |

Daily backup command (run by cron on the Neo4j host):

```bash
neo4j-admin database dump neo4j \
  --to-path=/backups/neo4j/$(date +%Y%m%d)/ \
  --overwrite-destination=true

# Upload to object store
mc cp --recursive \
  /backups/neo4j/$(date +%Y%m%d)/ \
  "minio/qa-os-traces/backups/neo4j/$(date +%Y%m%d)/"
```

### 2.2 RTO and RPO

| Metric | Target |
|--------|--------|
| **RPO** | ≤ 24 hours (daily dump) |
| **RTO** | ≤ 6 hours (restore + verify) |

For pre-migration snapshots: RPO = point-in-time at migration start.

### 2.3 Recovery Steps

#### Scenario A: Database corruption / accidental deletion

```bash
# 1. Stop Neo4j service
systemctl stop neo4j   # or docker stop neo4j-container

# 2. Identify the most recent valid backup
RESTORE_DATE="20260710"  # replace with actual date
BACKUP_PATH="/backups/neo4j/${RESTORE_DATE}/"

# If not on local disk, download from object store:
mc cp --recursive \
  "minio/qa-os-traces/backups/neo4j/${RESTORE_DATE}/" \
  /backups/neo4j/

# 3. Restore
neo4j-admin database load neo4j \
  --from-path="${BACKUP_PATH}" \
  --overwrite-destination=true

# 4. Start Neo4j
systemctl start neo4j

# 5. Verify connectivity
uv run python infra/neo4j/connectivity_check.py

# 6. Spot-check 3 random entities in Cypher browser or cypher-shell
cypher-shell -u neo4j "MATCH (n) RETURN n LIMIT 10"

# 7. Notify platform-team@qa-os.internal with:
#    - Estimated data loss window
#    - Node/relationship counts before vs. after restore
```

#### Scenario B: Full host failure

```bash
# 1. Provision replacement Neo4j Enterprise LTS 5.26.x host
# 2. Follow Neo4j Enterprise installation guide
# 3. Download latest backup from object store (step 2 above)
# 4. Restore using neo4j-admin database load (step 3 above)
# 5. Update NEO4J_URI in all service configs
# 6. Run connectivity check (step 5 above)
```

---

## 3. Backup Verification

Backups are **verified monthly** by restoring to a staging environment and running:

```bash
# 1. Restore to staging Neo4j instance
# 2. Run: uv run python infra/neo4j/connectivity_check.py
# 3. Run: uv run pytest packages/ -k "smoke" --tb=short
# 4. Document result in: infra/deploy/dr-drill-report.md
```

See [`infra/deploy/dr-drill-report.md`](./dr-drill-report.md) for the drill report template and last completed report.

---

## 4. Cross-Signed Approval

> **This policy requires sign-off from the Graph sub-lead before being considered active.**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Platform Lead | `<Platform Lead Name>` | `________________________` | `__________` |
| **Graph Sub-lead** | `<Graph Sub-lead Name>` | `________________________` | `__________` |
| Engineering Director | `<Director Name>` | `________________________` | `__________` |

---

## 5. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-07-11 | Platform Team | Initial policy. Closes Major Risk #8, Underengineering #2. |
