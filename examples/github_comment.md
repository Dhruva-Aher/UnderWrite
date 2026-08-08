## Underwrite: Governance Review Failed

**Deployment blocked.** Deterministic policy evaluation against DataHub lineage failed.

### Violation Summary
- **Policy:** ML-LEAK-001 (Target Leakage)
- **Reason code:** `TARGET_LEAKAGE`
- **Decision:** Block deploy (CI exit non-zero)
- **Evidence:** Serving feature derives from a column tagged `urn:li:tag:post_outcome`

### Evidence path (seeded live scenario)

```text
mlModel:churn_model_v2
  → mlFeature:discount_history
  → dataset:stg_billing
  → dataset:raw_billing
  → schemaField:retention_discount  (tag: post_outcome)
```

---
*Authorization came from DataHub FineGrainedLineage. AI remediation did not participate in this decision. Tag/incident/documentation writeback is a side effect.*
