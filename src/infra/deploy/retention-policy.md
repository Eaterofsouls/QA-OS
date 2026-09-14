# Trace Artifact Retention Policy v1.0

**Document ID:** PACK-01 / Prompt_0102  
**Status:** ACTIVE  
**Effective Date:** 2026-07-11  
**Owner:** Platform Team (`platform-team@qa-os.internal`)  
**Reviewers:** Engineering Lead, Compliance

---

## 1. Scope

This policy governs the retention of all trace artifacts stored in the primary object store for the AI QA Operating System.

| Setting | Value |
|---------|-------|
| **Bucket Name** | `qa-os-traces` |
| **S3 Endpoint** | `${S3_ENDPOINT_URL}` (default: `http://localhost:9000` for local; see `.env` for production) |
| **Object prefix** | `traces/` |
| **Bootstrap setup script** | `infra/deploy/s3_setup.py` |

---

## 2. Retention Window

> **Policy: 90-day flat retention window.**

All objects under the `traces/` prefix in the `qa-os-traces` bucket are retained for exactly **90 calendar days** from their `created_at` timestamp (embedded in object metadata).

Objects older than 90 days are eligible for **permanent deletion**.

### Lifecycle Rule (S3/MinIO)

```json
{
  "Rules": [
    {
      "ID": "qa-os-traces-90d-retention",
      "Status": "Enabled",
      "Filter": { "Prefix": "traces/" },
      "Expiration": { "Days": 90 }
    }
  ]
}
```

Apply this rule via:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --endpoint-url "${S3_ENDPOINT_URL}" \
  --bucket qa-os-traces \
  --lifecycle-configuration file://infra/deploy/lifecycle-rules.json
```

---

## 3. Storage Tiering: **NOT IMPLEMENTED IN V1**

> ⚠️ **NO storage tiering is implemented in V1.**

There is a single storage class for all trace artifacts.  There is no:
- Transition to cheaper storage tiers (e.g., S3 Glacier, MinIO STANDARD_IA)
- Object-level tiering by age
- Prefix-based tiering by module

### Tiering Deferral Rationale

Storage tiering introduces operational complexity (class transition errors, restore latency, cross-tier copy charges) that is not justified at current data volumes and cost levels.

### V1.1 Trigger Condition

Storage tiering **will be introduced in V1.1** when the following threshold is exceeded:

```
cost_per_gb_usd > $X
```

Where `$X` is determined by the Platform Team at the time the threshold is first crossed, based on actual observed per-GB costs in the `qa-os-traces` bucket over a rolling 30-day window.

The decision to enable tiering requires:
1. Platform Team identifies `cost_per_gb_usd > $X` in monthly cost report.
2. Engineering Lead approves the ADR for tiering configuration.
3. A V1.1 sprint item is created and scoped.

---

## 4. Legal Hold & Compliance Exceptions

If a specific trace artifact must be retained beyond 90 days for legal or compliance reasons, place an S3 Object Lock hold on it:

```bash
aws s3api put-object-legal-hold \
  --endpoint-url "${S3_ENDPOINT_URL}" \
  --bucket qa-os-traces \
  --key traces/<object-key> \
  --legal-hold Status=ON
```

Legal holds must be documented in the compliance register and reviewed quarterly.

---

## 5. Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-07-11 | Platform Team | Initial policy. 90-day flat window. No tiering in V1. |
