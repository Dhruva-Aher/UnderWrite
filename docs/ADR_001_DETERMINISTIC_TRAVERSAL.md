# ADR 001: Deterministic Lineage Traversal vs. Probabilistic LLM Reasoning for ML Governance Enforcement

## Context & Problem Statement
In automated ML deployment gates, governance decisions (blocking or approving model deployments) carry critical financial and operational risk. If a governance agent encounters a feature derived from post-outcome target leakage, approving the deployment leads to catastrophic failure in production. Conversely, falsely blocking a clean model disrupts deployment pipelines.

We needed to decide whether policy enforcement (lineage graph traversal and rule evaluation) should be performed by an LLM or by a deterministic graph traversal algorithm.

## Decision Drivers
1. **Zero Hallucination Tolerance**: Deployment gates cannot tolerate non-deterministic false approvals caused by LLM hallucination or context window truncation.
2. **Auditability & Reproducibility**: Every governance verdict must be 100% reproducible given the exact same DataHub graph state.
3. **Execution Latency**: CI/CD deployment gates must not become a bottleneck in the pipeline. Traversal runs in-memory over an already-acquired subgraph so that evaluation cost is dominated by metadata acquisition, not by policy logic.
4. **DataHub Lineage Structure**: DataHub provides structured `FineGrainedLineage` aspects through its Python SDK, which form a directed graph suitable for standard graph search algorithms.

## Considered Options
1. **Option A: Pure LLM Agent** — Feed raw lineage metadata into an LLM prompt and ask the LLM to decide if target leakage exists.
2. **Option B: Pure Static Regex Rules** — Check column names against a static list of regex patterns in CI/CD scripts.
3. **Option C: Deterministic policy configuration (Selected)** — Load structured YAML policy definitions and evaluate them with a pure Python Depth-First Search (DFS) engine over an in-memory `InternalGraph` normalized from DataHub.

## Decision Outcome
**Chosen Option: Option C (Hybrid Architecture)**

### Rationale
- **Enforcement is 100% Deterministic**: The `agent.py` engine normalizes DataHub aspects into `InternalGraph` and executes cycle-safe DFS traversal (max depth: 6 hops). Zero LLM calls occur during graph traversal or verdict evaluation.
- **Latency & Reliability**: Traversal has no runtime dependency on an LLM provider; DataHub acquisition latency remains external to the traversal step.
- **DataHub Write-Back**: Verdict evidence paths (`EvidencePath`) are deterministically constructed and written back as DataHub `GlobalTags`, `IncidentInfo`, and `InstitutionalMemory` entries.

## Status
**Decided & Implemented** (Frozen Architecture).
