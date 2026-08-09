# Sample outputs

Unedited captures from a live run against a seeded DataHub GMS quickstart. Every
file here was produced by piping the real `POST /evaluate` response or the real
`scripts/deployment_gate.py` stdout to disk — nothing is hand-authored, so the
shapes match what the console and CI actually receive.

They let a judge inspect real responses **without** standing up DataHub GMS.

| File | Model | Result |
| --- | --- | --- |
| `blocked_evaluate_response.json` | `churn_model_v2` | `blocked` / `TARGET_LEAKAGE`, evidence to `raw_billing.retention_discount` |
| `approved_evaluate_response.json` | `recommendation_model_v1` | `approved` / `CLEAN`, 3 policies evaluated, no evidence paths |
| `incomplete_lineage_evaluate_response.json` | `fraud_model_v3` | `blocked` / `INCOMPLETE_LINEAGE` — fail-closed on an unresolvable graph |
| `gate_blocked_exit1.txt` | `churn_model_v2` | Deployment gate CLI, process exit **1** |
| `gate_approved_exit0.txt` | `recommendation_model_v1` | Deployment gate CLI, process exit **0** |

All three JSON payloads carry `evaluation_source: live_datahub`, which is the
only source the gate will approve on. They are **not** the offline synthetic
fixture (`demo/fixtures/…` / `customer_status`).

To regenerate after a code change:

```bash
python seed.py                       # seed DataHub GMS
python -m uvicorn app:app --port 8000
curl -s -X POST localhost:8000/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"model_urn":"urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"}' \
  | python -m json.tool > examples/sample_outputs/blocked_evaluate_response.json
```
