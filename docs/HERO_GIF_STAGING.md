# Underwrite: Hero GIF Staging

**Goal:** A ≤10s loop that communicates: *DataHub lineage → CI blocks unsafe ML deploy.*

Align with the product: **target leakage via FineGrainedLineage**, not a SQL column-drop story.

## Setup
1. DataHub UI (seeded) open — show the leak path on `churn_model_v2`.
2. Terminal with live `python demo/run_demo.py` ready (GMS up).
3. Optional: GitHub Actions / gate red check on the right.

## 10-Second Script

**0:00 – 0:03 (The lie in the code)**  
Feature / training snippet looks clean. Overlay: "Looks safe in code."

**0:03 – 0:07 (DataHub knows)**  
Cut to DataHub lineage: outcome column → rename → aggregate → feature → model. Overlay: "DataHub sees the path."

**0:07 – 0:10 (Enforce)**  
Terminal or CI: **BLOCKED** + evidence path + non-zero exit. Overlay: "Underwrite fails the deploy."

## Post-Processing
- Prefer crisp terminal/DataHub UI over IDE theater.
- Export `< 5MB` for Devpost/README load.
- Never show the offline mock labeled as live DataHub.
