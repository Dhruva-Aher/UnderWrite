# Metrics & Claims — Underwrite

**Cross-verified:** 2026-09-30  
Prefer tag `freeze-grand-prize-ready` for judge reproduction.

| ID | Claim (exact) | Grade | Evidence |
|----|---------------|-------|----------|
| C1 | Authorization is **deterministic** over DataHub lineage; LLM never authorizes | A | ADR_001; `agent` policy engine; README |
| C2 | Captured evaluate: **blocked** / TARGET_LEAKAGE, latency_ms **245** | A | `examples/sample_outputs/blocked_evaluate_response.json` |
| C3 | Captured evaluate: **approved** / CLEAN, latency_ms **110** | A | `examples/sample_outputs/approved_evaluate_response.json` |
| C4 | Captured evaluate: **blocked** / INCOMPLETE_LINEAGE, latency_ms **29** | A | `examples/sample_outputs/incomplete_lineage_evaluate_response.json` |
| C5 | Console screenshots of blocked/approved decisions | A | `docs/screenshots/` |
| C6 | Offline demo cannot produce CI approval | A | README eval table; `demo/run_demo.py --offline` |
| C7 | Write-back of governance decision to DataHub | A | writeback design + sample `write_back` fields |
| C8 | GitHub Actions CI on `main` | D | **No** `.github/workflows` on remote (2026-09-30) — do not show CI badge |

## Non-claims

| Phrase | Why |
|--------|-----|
| Latency_ms as DataHub SLA | Captured against seeded quickstart; acquisition-dominated |
| “Blocks X% of unsafe models in prod” | Demo/seed graph, not fleet metrics |

## Re-verify

```bash
git checkout freeze-grand-prize-ready
# Inspect examples/sample_outputs/*.json
python demo/run_demo.py --offline
```
