## Underwrite: Governance Review Failed

**Deployment blocked.** Deterministic policy evaluation against DataHub lineage failed.

### Violation Summary
- **Policy:** ML-LEAK-001 (Target Leakage)
- **Reason code:** `TARGET_LEAKAGE`
- **Decision:** Block deploy (CI exit non-zero)
- **Evidence:** Serving feature derives from a column tagged `urn:li:tag:post_outcome` through a non-anonymizing transform

### Evidence path (sample)

```text
mlModel:churn_model_v2
  → mlFeature:feature1
  → dataset:model_input
  → dataset:intermediate
  → schemaField:status_cleaned
  → schemaField:customer_status  (tag: post_outcome)
```

---
*Authorization came from DataHub FineGrainedLineage. AI remediation did not participate in this decision. An incident/tag writeback is scheduled as a side effect.*
