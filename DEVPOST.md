# Devpost: Underwrite

**Headline**: DataHub knows where your ML features came from. Underwrite makes CI act on that knowledge.

**Elevator Pitch**: Underwrite turns DataHub lineage into a CI authorization boundary for ML deployments. Target leakage is the demonstration; metadata-backed deployment authorization is the product.

**Verified release pin (judge checkout):** tag [`freeze-grand-prize-ready`](https://github.com/Dhruva-Aher/UnderWrite/tree/freeze-grand-prize-ready). Prefer this tag over drifting `main` so you land on the exact state that passed live GMS verification (blocked `TARGET_LEAKAGE`, writeback SUCCESS, deployment gate exit 1, console renders the lineage graph).

## The Problem

**A machine learning model cannot unsee data.**

If forbidden data (like a future outcome) leaks into training features, the model is corrupted. Renames, aggregates, and feature stores hide the relationship from code review. Traditional CI cannot see it. Dashboards cannot stop it.

You cannot solve this by looking at dashboards. **You solve it by breaking the build.**

## The Solution: Metadata-backed deployment authorization

Underwrite is an ML deployment agent that converts DataHub's context graph into a deployment decision:

```text
SAFE   → deployment continues (exit 0)
UNSAFE → deployment terminates (exit non-zero)
```

```text
Observe → Reason → Act → Remember → Assist
DataHub   Trace +   Block    Write to    ACK remediation
context   policy    deploy   DataHub     (after a block)
```

**Target leakage is the concrete policy demonstrated.** The core abstraction is metadata-backed deployment authorization: DataHub provides the evidence; Underwrite decides; CI enforces. The LLM never authorizes.

### Phase 1 — Deterministic Enforcement (Safety)

Underwrite acquires DataHub aspects, normalizes them into an in-memory graph, then evaluates policy over that evidence. The authorization verdict does not depend on an LLM. Fail-closed: even an `approved` payload cannot deploy unless `evaluation_source == live_datahub`.

### Phase 2 — Generative Remediation (Velocity)

Only after a block does the AI Remediation Advisor receive the immutable evidence bundle. It uses the DataHub Agent Context Kit with `include_mutations=False`. AI augments recovery; it never authorizes.

## Why DataHub?

Target leakage hides inside multi-hop transformations where column names change. DataHub's FineGrainedLineage, schema-field entities, GlobalTags, and GlossaryTerms make that path queryable. Underwrite **reads** that graph for the verdict and **writes** incidents/tags/documentation back — authorization and catalog mutation stay separate.

**Thesis:** DataHub provides the evidence. Underwrite decides. CI enforces.

## Demo framing

1. Open on **DataHub** lineage for `churn_model_v2` — it already looks legitimate until you walk upstream.
2. Underwrite finds the poisoned ancestor, **blocks**, and write-back appears (incident / governance memory).
3. Cut to `churn_model_v2_fixed` → **approved** — same gate, not always-red.
4. One architecture beat, then back to the product. No DFS / stack tour.

Full beat sheet: [`docs/DEMO_SCREENPLAY.md`](docs/DEMO_SCREENPLAY.md).

## Sample outputs (no GMS required to inspect)

See [`examples/sample_outputs/`](examples/sample_outputs/) for a captured live-shaped `POST /evaluate` blocked payload (`evaluation_source=live_datahub`, evidence to `raw_billing.retention_discount`) and a gate exit excerpt. These are **not** the offline fixture.

## Open-source contribution (DataHub)

UnderWrite is itself Apache 2.0. Beyond the project, the workflow is being upstreamed into the DataHub ecosystem:

| Contribution | Link |
| --- | --- |
| **Skills proposal** — `datahub-ml-leakage` | [datahub-skills#136](https://github.com/datahub-project/datahub-skills/issues/136) |
| **Skills PR** — full `SKILL.md` + routing + templates | [datahub-skills#137](https://github.com/datahub-project/datahub-skills/pull/137) |
| **Core API issue** — batch `schemaField` tag/term fetch for FineGrainedLineage policy walks | [datahub#19060](https://github.com/datahub-project/datahub/issues/19060) |

The skill encodes the same invariants as this service: deterministic traversal, fail-closed incomplete lineage, LLM never authorizes, write-backs as approval-gated side effects. Agent Context Kit is used for remediation only (`include_mutations=False`).
