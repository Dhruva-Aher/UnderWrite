# Underwrite — Core System Invariants

> **System Invariants & Regression Checklist**

1. **Verdict Determinism**: Verdicts are deterministic functions of graph metadata. Given the same graph, the verdict is identical.
2. **Traversal Decoupling**: Graph traversal operates strictly on in-memory `InternalGraph` representations and NEVER performs SDK calls.
3. **Fail-Closed Default**: Missing, incomplete, or unresolvable lineage ALWAYS produces a `blocked` verdict (`INCOMPLETE_LINEAGE`).
4. **Write-Back Independence**: Write-back is a pure side effect. Verdict generation and UI rendering NEVER depend on write-back success or speed.
5. **Evidence Traceability**: Every blocked verdict carries evidence paths reconstructed from the acquired DataHub graph — never fabricated blast-radius or risk scores.
6. **Demo Reproducibility**: The demonstrated target-leakage scenario (`churn_model_v2` → `discount_history` → `raw_billing.retention_discount`) is reproducible offline via `demo/fixtures/` and online via `seed.py` against live GMS. Additional seeded models (`recommendation_model_v1`, `fraud_model_v3`) exist for approved / incomplete-lineage checks; they are not required for the primary judge path.
