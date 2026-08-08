# Sample outputs (submission insurance)

Captured shape from the **verified live** path pinned at tag `freeze-grand-prize-ready`.

These files let a judge inspect the real blocked-response shape **without** standing up DataHub GMS.

| File | What it shows |
| --- | --- |
| `blocked_evaluate_response.json` | `POST /evaluate` body: `evaluation_source=live_datahub`, `TARGET_LEAKAGE`, evidence paths to `retention_discount` |
| `gate_exit_excerpt.txt` | Deployment gate CLI for the same model: process exit **1** |

**Not** the offline synthetic fixture (`demo/fixtures/…` / `customer_status`). Judge-facing vocabulary is the seeded live scenario only.
