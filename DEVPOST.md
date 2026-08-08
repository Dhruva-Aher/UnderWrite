# Devpost: Underwrite

**Headline**: Underwrite turns DataHub lineage into a CI authorization boundary for ML deployments.

**Elevator Pitch**: An ML feature can look safe in code while three transformations upstream it derives from post-outcome data. Underwrite traverses DataHub's column lineage, deterministically fails the deployment, and only then uses AI to explain remediation.

**Verified release pin (judge checkout):** tag [`freeze-grand-prize-ready`](https://github.com/Dhruva-Aher/UnderWrite/releases/tag/freeze-grand-prize-ready) · commit `f09ad46`. Prefer this tag over drifting `main` so you land on the exact state that passed live GMS verification (blocked `TARGET_LEAKAGE`, writeback SUCCESS, deployment gate exit 1).

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

Underwrite acquires DataHub aspects, normalizes them into an in-memory `InternalGraph`, then runs a cycle-safe DFS. **The authorization verdict does not depend on an LLM.** Mid-traversal never calls the SDK again — that keeps the gate deterministic and inspectable. Fail-closed: even an `approved` payload cannot deploy unless `evaluation_source == live_datahub`.

### Phase 2 — Generative Remediation (Velocity)

Only after a block does the AI Remediation Advisor receive the immutable evidence bundle. It uses the DataHub Agent Context Kit with `include_mutations=False`. AI augments recovery; it never authorizes.

## Why DataHub?

Target leakage hides inside multi-hop transformations where column names change. DataHub's FineGrainedLineage, schema-field entities, GlobalTags, and GlossaryTerms make that path queryable. Underwrite **reads** that graph for the verdict and **writes** incidents/tags/documentation back — authorization and catalog mutation stay separate.

**Thesis:** DataHub already knows how your data is connected. Underwrite makes that knowledge enforceable.

## Demo framing (same system — agentic sequencing)

Lead with DataHub’s lineage graph (inert), then show the agent walking it, finding `retention_discount` multi-hop upstream, blocking, and writing tag/incident back — exit code is confirmation, not the hero shot. Cut `churn_model_v2` (blocked + named incident) against `churn_model_v2_fixed` (approved) back-to-back so the gate is visibly not always-red. Full beat sheet: [`docs/DEMO_SCREENPLAY.md`](docs/DEMO_SCREENPLAY.md).

## Sample outputs (no GMS required to inspect)

See [`examples/sample_outputs/`](examples/sample_outputs/) for a captured live-shaped `POST /evaluate` blocked payload (`evaluation_source=live_datahub`, evidence to `raw_billing.retention_discount`) and a gate exit excerpt. These are **not** the offline fixture.
