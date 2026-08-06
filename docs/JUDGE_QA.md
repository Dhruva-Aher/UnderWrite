# Underwrite — Technical Judge Q&A Reference

This document provides exact, objective answers to technical judging questions regarding Underwrite's architecture, DataHub integration, and design decisions.

---

### Q1: Why DataHub instead of OpenMetadata or Neo4j?
**Answer**:
DataHub provides out-of-the-box cross-warehouse column-level lineage (`FineGrainedLineage`) connecting dbt transformations, Snowflake tables, Feature Stores, and MLflow model entities. OpenMetadata and traditional graph databases (Neo4j) lack standard native schema classes for MLModel, MLFeature, and bidirectionally coupled Dataset Incidents. DataHub serves as the enterprise metadata plane where governance memory persists natively.

---

### Q2: Why not enforce this inside CI/CD without a metadata platform?
**Answer**:
Static CI/CD linters examine code syntax inside a single repository (e.g., SQL queries or Python scripts). They cannot resolve cross-system column lineage such as `raw_billing.retention_discount` flowing to `stg_billing.discount_history`. Underwrite relies on the metadata graph that DataHub exposes to the SDK.

---

### Q3: How do you handle incomplete or unresolvable lineage?
**Answer**:
Underwrite enforces a **fail-closed governance strategy**. If graph traversal encounters an untracked upstream source or broken lineage node, it produces an `INCOMPLETE_LINEAGE` verdict (`blocked`). Unresolvable metadata is treated as a security boundary violation until provenance is proven.

---

### Q4: What happens if two policies disagree?
**Answer**:
Underwrite follows a strict **pessimistic evaluation rule**. If any policy returns a `BLOCKED` verdict (`TARGET_LEAKAGE` or `INCOMPLETE_LINEAGE`), the deployment request is blocked. Approval requires 100% policy compliance across all active rules.

---

### Q5: Can Underwrite support new policy types?
**Answer**:
Yes. **We demonstrate separating** graph traversal from rule evaluation via `PolicyEvaluator` and `policies.yaml`. New rules (e.g., PII/GDPR data access restrictions or temporal timestamp boundaries) are added by defining target tags and predicates in `policies.yaml` without changing graph search code.

---

### Q6: Why Depth-First Search (DFS) instead of Breadth-First Search (BFS)?
**Answer**:
DFS naturally reconstructs end-to-end evidence chains from the model root down to the root tainted table field. When a policy violation is detected, DFS preserves the exact sequence of hops (`[model -> feature -> mart -> raw_table]`), providing immediate audit evidence. DFS uses in-memory recursion with cycle tracking and a maximum depth cap of 6.

---

### Q7: How does this scale with larger lineage graphs?
**Answer**:
**We demonstrate separating** **Graph Acquisition** from **Graph Traversal**:
1. Acquisition fetches up to six upstream dataset hops relevant to the target model URN through the DataHub Python SDK.
2. Traversal operates in-memory on the normalized sub-graph (`InternalGraph`); no latency target is asserted by this repository.
3. Write-backs run asynchronously as non-blocking side effects after the HTTP verdict is returned.

---

### Q8: What assumptions does correctness depend on?
**Answer**:
Correctness depends on:
1. DataHub holding accurate column-level lineage metadata (`FineGrainedLineage`).
2. Source datasets tagged with governance tags (`post_outcome`, `is_target`).
3. CI/CD pipelines routing deployment requests through Underwrite's `/evaluate` gate.
