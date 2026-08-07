# Underwrite: Devpost A/B Test

To optimize the Devpost submission, we have created two versions. 
**Version A** focuses on technical credibility (Engineer-focused). 
**Version B** focuses on business impact and actionable metadata (Judge-focused).

After review, we will submit the version that most effectively answers the judge's questions in the first 30 seconds.

---

## Version A: Engineer-Focused

**Headline**: Underwrite: Deterministic Deployment Gates via AST Parsing and DataHub Lineage

**Elevator Pitch**: Target leakage destroys ML models. Underwrite solves this by intercepting CI/CD, parsing semantic SQL diffs, and traversing the DataHub lineage graph to block breaking changes deterministically.

### 🚨 The Technical Problem
When a developer drops a column, standard CI only checks if the local `dbt` model compiles. It is completely blind to the downstream metadata graph. A column drop can silently corrupt a production machine learning model, causing severe target leakage.

### 💡 The Solution: Deterministic CI + Agentic Remediation
Underwrite introduces a two-phase architecture:
1. **Deterministic Enforcement**: We parse the PR using `sqlglot` to generate a semantic AST diff. We then query the DataHub Fine-Grained Lineage API, performing a cycle-safe DFS traversal to calculate the exact blast radius. If forbidden downstream nodes are affected, the build is hard-blocked.
2. **Agentic Remediation**: An AI agent reads the DataHub metadata to find alternative columns and drafts a remediation PR comment.

### 🔗 Why DataHub?
DataHub is the only catalog with real-time Fine-Grained Lineage APIs capable of powering a sub-100ms deployment gate. We don't just read DataHub; we write Incidents back to it via the Python SDK, turning it into the operational brain of the pipeline.

---

## Version B: Judge-Focused (Recommended)

**Headline**: Underwrite: Metadata-aware CI that blocks breaking pull requests.

**Elevator Pitch**: We use metadata to stop bad deployments. Underwrite prevents engineers from accidentally destroying downstream ML models and dashboards by checking the DataHub lineage graph before they merge.

### 🚨 The Problem: CI is Blind to Metadata
A machine learning model cannot unsee data. If an engineer accidentally removes a critical column in a pull request, traditional CI (like GitHub Actions) will pass as long as the code compiles. 

By the time the data reaches the ML model, it's corrupted. The only way to stop this is to block the build.

### 💡 The Solution: Actionable Metadata
Underwrite turns DataHub from a passive catalog into an active deployment gate.

**1. The Safety Gate (Deterministic)**: 
When a PR is opened, Underwrite calculates the blast radius using DataHub's real-time lineage. If the PR breaks a downstream ML model, it fails the GitHub Action immediately. No heuristics, no AI hallucinations. Just a deterministic block.

**2. The Velocity Fix (AI)**:
Once safely blocked, our read-only AI agent investigates DataHub to find the approved alternative column, drafting a ready-to-merge fix directly in the PR comment.

### 🔗 Built on DataHub
Underwrite was built specifically for the DataHub ecosystem. It leverages the Fine-Grained Lineage API for the safety gate, and it writes back native "Incidents" to DataHub to alert stakeholders when a model is under threat from an active PR.

---

## Decision
**We recommend Version B**. It strictly adheres to the "Judge Memory" anchor and frames the problem emotionally ("CI is blind") before explaining the architecture. It proves that the tool makes metadata *actionable*.
