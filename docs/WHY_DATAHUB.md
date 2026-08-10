# Why DataHub? Architectural Rationale & Alternatives Comparison

**Underwrite demonstrates relying** on DataHub as both a **metadata source** and a **governance memory destination**. This document details why DataHub provides the fine-grained lineage model and APIs that make this implementation practical without building a metadata platform from scratch.

---

## 1. The Core Differentiator: Column-Level Lineage (`FineGrainedLineage`)

Target leakage rarely manifests at the top-level dataset schema. Instead, it occurs deep inside multi-hop transformation pipelines where column names change across dbt models, views, and feature stores.

### Column Transformation Chain Example:
```
[raw_billing.retention_discount] (Tagged: post_outcome)
               │
               ▼ (dbt staging view)
[stg_user_discounts.discount_amt]
               │
               ▼ (dbt mart model)
[fct_user_summary.user_discount]
               │
               ▼ (Feature Store ingest)
[churn_features.discount_history] (Used in ML model)
```

### Why Flat Tag Checks Fail:
If a governance tool only checks tags directly on `churn_features` or `churn_model_v2`, it finds zero tags. The feature appears clean.

### Why DataHub Lineage Succeeds:
DataHub captures fine-grained, column-level lineage (`FineGrainedLineage`) across transformations and data platforms. We demonstrate reading available field lineage and field tags, tracing `stg_billing.discount_history` to `raw_billing.retention_discount`, which carries the `post_outcome` tag.

---

## 2. Semantic Governance: Tags vs. Glossary Terms

While many tools treat governance as simple string-matching, DataHub provides robust semantic primitives. Underwrite integrates deeply with both:
- **GlobalTags**: Ad-hoc, flexible labels (e.g., `post_outcome`, `is_target`).
- **GlossaryTerms**: Strongly typed, hierarchical, centrally managed business vocabulary (e.g., `urn:li:glossaryTerm:PostOutcome`).

Underwrite normalizes both into its internal graph and surfaces them on every evaluated node. The demonstrated policy evaluates GlobalTags; GlossaryTerms are acquired and displayed as evidence context, and are the natural next predicate for the same traversal.

---

## 3. Governance Memory: From Intercept to Organizational Knowledge

Most CI/CD checks return a transient status code (`0` or `1`) that disappears when the build pipeline closes. **We demonstrate converting** deployment verdicts into **governance memory** inside DataHub:

```
[MLModel] ──► [MLFeature] ──► [Dataset]
   │                             │
   ▼                             ▼
[GlobalTags]               [IncidentInfo]
(model-at-risk)            (Target Leakage)
   │
   ▼
[InstitutionalMemory]
(Audit Link & Rationale)
```

When DataHub accepts the requested write-back, governance evidence is recorded against the relevant entities for later catalog inspection.

---

## 4. Alternatives Comparison Matrix

| Alternative Approach | Primary Limitation | Underwrite + DataHub Architecture |
| :--- | :--- | :--- |
| **Static Code Linter** (e.g., SQLFluff) | Cannot trace runtime lineage across heterogeneous tools (dbt to Snowflake to MLflow). | DataHub unifies cross-platform metadata into a single searchable lineage graph. |
| **Data Quality Framework** (e.g., Great Expectations) | Checks data value distributions (NULLs, bounds), not temporal provenance. | Target leakage features often look statistically valid; Underwrite checks structural lineage. |
| **Data Observability** (e.g., Monte Carlo) | Detects anomalies *after* data reaches production. | Underwrite evaluates a deployment request before a caller chooses whether to deploy. |
| **Custom Graph Database** (e.g., Neo4j) | Requires building custom connectors, catalog UI, and entity models from scratch. | DataHub provides metadata ingestion, a Python SDK, REST services, and entity models. |
| **Alternative Catalogs** (e.g., OpenMetadata, Amundsen) | Differing API schemas and less fine-grained ML entity support (`MLModel`, `MLFeature`). | DataHub offers native ML entity abstractions and fine-grained column lineage primitives. |
