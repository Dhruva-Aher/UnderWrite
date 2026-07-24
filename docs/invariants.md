# Underwrite — Core System Invariants

> **System Invariants & Regression Checklist**

1. **Verdict Determinism**: Verdicts are 100% deterministic functions of graph metadata. Given the same graph, the verdict is identical.
2. **Traversal Decoupling**: Graph traversal operates strictly on in-memory `InternalGraph` representations and NEVER performs SDK calls.
3. **Fail-Closed Default**: Missing, incomplete, or unresolvable lineage ALWAYS produces a `blocked` verdict (`INCOMPLETE_LINEAGE`).
4. **Write-Back Independence**: Write-back is a pure side effect. Verdict generation and UI rendering NEVER depend on write-back success or speed.
5. **Evidence Traceability**: Every verdict can be completely reconstructed and verified from audit paths in the graph evidence.
6. **Demo Scenario Reproducibility**: All 3 demo scenarios (`churn_model_v2`, `recommendation_model_v1`, `fraud_model_v3`) are 100% reproducible offline and online.
