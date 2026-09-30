# Decisions — Underwrite

Related: [METRICS.md](./METRICS.md) · [ADR_001_DETERMINISTIC_TRAVERSAL.md](./ADR_001_DETERMINISTIC_TRAVERSAL.md) · [invariants.md](./invariants.md)

**Cross-verify (2026-09-30):** Sample evaluate JSON verdicts + latencies Grade **A**. GitHub Actions CI added (unit + offline demo). Local unit run: **49 passed**.

---

## D1 — Deterministic traversal authorizes; LLM assists only

| | |
|--|--|
| **Context** | LLM-as-judge can hallucinate “safe” under target leakage. |
| **Decision** | Fail-closed DFS/policy engine over DataHub graph; LLM for explanation/remediation assist, never for allow. |
| **Why** | Zero hallucination tolerance on deploy gates. |
| **Alternatives** | Pure LLM; regex-only column denylist. |
| **Evidence** | ADR_001; METRICS C1–C4 |
| **Status** | DECIDED · IMPLEMENTED · VERIFIED (samples) |

---

## D2 — Observe → Reason → Act → Remember → Assist loop

| | |
|--|--|
| **Context** | One-shot block without write-back loses institutional memory. |
| **Decision** | Block in CI and write verdict evidence back to DataHub (tags/incidents/memory). |
| **Evidence** | writeback_design.md; sample `write_back` |
| **Status** | DECIDED · IMPLEMENTED |

---

## D3 — Pin a freeze tag for judges

| | |
|--|--|
| **Context** | `main` drifts; hackathon judges need a fixed SHA. |
| **Decision** | Prefer `freeze-grand-prize-ready` + checked-in sample outputs / screenshots. |
| **Evidence** | README pin table |
| **Status** | DECIDED · IMPLEMENTED |

---

## D4 — Offline path cannot approve

| | |
|--|--|
| **Context** | Offline demo without live GMS must not fake CI green. |
| **Decision** | Offline sanity exercises policy engine but cannot produce approval. |
| **Evidence** | README evaluation table |
| **Status** | DECIDED · IMPLEMENTED |

---

## D5 — Incomplete lineage fails closed

| | |
|--|--|
| **Context** | Missing edges could hide leakage. |
| **Decision** | Incomplete lineage → **blocked** (sample reason INCOMPLETE_LINEAGE). |
| **Evidence** | sample_outputs incomplete_lineage |
| **Status** | DECIDED · IMPLEMENTED · VERIFIED |

---

## D6 — CI runs offline unit tests without live DataHub

| | |
|--|--|
| **Context** | Full verify.sh needs python3.13 venv + optional Docker; recruiters need a green badge. |
| **Decision** | GitHub Actions: `pytest tests/unit` (+ invariant/trust/gate modules) and `demo/run_demo.py --offline`. Live GMS integration stays optional/local. |
| **Evidence** | `.github/workflows/ci.yml`; 49 unit tests passed locally 2026-09-30 |
| **Status** | DECIDED · IMPLEMENTED |

