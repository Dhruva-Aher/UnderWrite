# Devpost: Underwrite

**Headline**: Underwrite turns DataHub lineage into a CI authorization boundary for ML deployments.

**Elevator Pitch**: An ML feature can look safe in code while three transformations upstream it derives from post-outcome data. Underwrite traverses DataHub's column lineage, deterministically fails the deployment, and only then uses AI to explain remediation.

## The Problem

**A machine learning model cannot unsee data.**

If forbidden data (like a future outcome) leaks into training features, the model is corrupted. Renames, aggregates, and feature stores hide the relationship from code review. Traditional CI cannot see it. Dashboards cannot stop it.

You cannot solve this by looking at dashboards. **You solve it by breaking the build.**

## The Solution: Metadata as Executable Infrastructure

Underwrite converts DataHub's context graph into a deployment decision:

```text
SAFE   → deployment continues (exit 0)
UNSAFE → deployment terminates (exit non-zero)
```

**Target leakage is the concrete policy demonstrated.** The core abstraction is metadata-backed deployment policy enforcement: DataHub evidence authorizes; AI never decides.

### Phase 1 — Deterministic Enforcement (Safety)

Underwrite traverses `UpstreamLineage.fineGrainedLineages` with a cycle-safe DFS. **The authorization verdict does not depend on an LLM.** Fail-closed: even an `approved` payload cannot deploy unless `evaluation_source == live_datahub`, so cached or spoofed results cannot bypass the gate.

### Phase 2 — Generative Remediation (Velocity)

Only after a block does the AI Remediation Advisor receive the immutable evidence bundle. It uses the DataHub Agent Context Kit with `include_mutations=False` and formats deterministic evidence into markdown recovery advice. AI augments recovery; it never authorizes.

## Why DataHub?

Target leakage hides inside multi-hop transformations where column names change. DataHub's FineGrainedLineage, schema-field entities, GlobalTags, and GlossaryTerms make that path queryable. Underwrite reads that graph for the verdict and writes incidents/tags back as side effects — authorization and catalog mutation stay separate concerns.

**Thesis:** DataHub already knows how your data is connected. Underwrite makes that knowledge enforceable.
