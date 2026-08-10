# Underwrite: Demo Screenplay (≤ 3 minutes)

**Pin:** record from tag `freeze-grand-prize-ready`.  
**Hard limit:** judges need not watch past three minutes.  
**Thesis:** *DataHub already knows how your data is connected. Underwrite makes that knowledge enforceable in CI.*

Live GMS only. Never show the offline fixture.  
**Pair:** `churn_model_v2` (blocked) ↔ `churn_model_v2_fixed` (approved).  
**Vocabulary:** `churn_model_v2` → `discount_history` → … → `raw_billing.retention_discount` (`post_outcome`).

**Framing rule:** Lead with the **graph**, not the terminal. Sequence every beat as *autonomous agent work*: see lineage → walk it → decide → write back. The exit code is proof *after* the agent story, not the hero image.

---

### **0:00–0:25 | Cold open — inert graph → agent walks it**
**Show (silent first):** DataHub lineage for `churn_model_v2` — the graph sitting there, inert. Pan/zoom toward the multi-hop path ending at `retention_discount` / `post_outcome`.  
**Then narrate over the same UI as write-back lands:** tag `model-at-risk` + named incident appearing.  
**Say:** "This lineage already lived in DataHub. The agent walks the graph on its own, finds the tainted column several transformations upstream, decides to block the deploy, and writes the verdict back."  
**Optional beat (≤3s):** Cut to terminal only long enough to flash `GATE_EXIT=1` / `evaluation_source=live_datahub` — confirmation, not the open.

### **0:25–0:40 | Why InternalGraph (once — trust, not theater)**
**Say:** "It acquires from DataHub once into an in-memory graph, then evaluates with no LLM in the decision and no live SDK calls mid-traversal. Deterministic authorization; DataHub stays the source of truth."

### **0:40–0:55 | Counterfactual (the flashy hook)**
**Show back-to-back, same cadence:**  
1. `churn_model_v2` → blocked, named incident / `model-at-risk`.  
2. `churn_model_v2_fixed` → approved, sails through (exit 0 / clean tag).  
**Say:** "Same team, same day, same gate. One model gets blocked with a named incident. The other sails through clean."  
Do not explain DFS here — the contrast *is* the argument.

### **0:55–2:20 | Walkthrough (one blocked path, then breathe)**
**Show:** Evidence path on the blocked model ending at `raw_billing.retention_discount`. Brief remediation/advisor beat only if it stays under the clock (AI explains *after* the block — never authorizes).  
**Say:** "The feature looked safe in code. Column lineage made the leak enforceable."

### **2:20–2:50 | Trust the artifact**
**Show:** Repo pin/tag `freeze-grand-prize-ready`, `examples/sample_outputs/`, tests, LICENSE.  
**Say:** "Judges can inspect the captured live payload without standing up GMS — and reproduce from this tagged commit."

### **2:50–3:00 | Thesis**
**On screen:** Underwrite.  
**Say:** "DataHub already knows how your data is connected. Underwrite makes that knowledge enforceable in CI."

---

## Checklist
- [ ] Recording from `freeze-grand-prize-ready`
- [ ] **Opens on DataHub lineage graph**, not a terminal wall of text
- [ ] Narration = walk → find → decide → write back (agentic sequence)
- [ ] `churn_model_v2` vs `churn_model_v2_fixed` cut back-to-back (~15s)
- [ ] Gate exit **1** only as proof beat for blocked (not the cold open)
- [ ] Writeback (tag + incident) visible in DataHub UI
- [ ] No `customer_status` / offline fixture vocabulary
- [ ] InternalGraph said once only
