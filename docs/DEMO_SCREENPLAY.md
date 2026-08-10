# Underwrite: Demo Screenplay (≤ 3 minutes)

**Pin:** record from tag `freeze-grand-prize-ready`.  
**Hard limit:** judges need not watch past three minutes.  
**Thesis:** *DataHub knows where your ML features came from. Underwrite makes CI act on that knowledge.*

Live GMS only. Never show the offline fixture.  
**Pair:** `churn_model_v2` (blocked) ↔ `churn_model_v2_fixed` (approved).  
**Vocabulary:** `churn_model_v2` → `discount_history` → … → `raw_billing.retention_discount` (`post_outcome`).

**Framing rule:** Open on **DataHub**, not Underwrite UI. Behavior over implementation. Never narrate DFS, FastAPI, Pydantic, React, LangChain, or DI.

```text
Observe → Reason → Act → Remember → Assist
```

---

### **0:00–0:30 | Cold open — DataHub first**
**Show:** DataHub UI lineage for `churn_model_v2`. Zoom the multi-hop path toward `retention_discount` / `post_outcome`.  
**Say:** "DataHub already knows something CI doesn't. This feature looks safe in code. Three transformations upstream, it derives from post-outcome data."  
Do **not** open on the Underwrite console or a terminal wall.

### **0:30–1:00 | Act + Remember (block → write-back)**
**Show:** Underwrite evaluates → **DEPLOYMENT BLOCKED**. Immediately cut back to DataHub: before (lineage only) vs after (incident / `model-at-risk` / governance memory).  
**Say:** "Underwrite walks that provenance, blocks the deploy, and writes the decision back into DataHub."  
**Optional ≤3s proof:** flash `GATE_EXIT=1` / `evaluation_source=live_datahub` — confirmation, not the hero.

### **1:00–1:25 | Counterfactual (not always-red)**
**Show back-to-back:**  
1. `churn_model_v2` → blocked + named incident.  
2. `churn_model_v2_fixed` → approved (exit 0 / clean).  
**Say:** "Same gate, same day. Target leakage is the demonstration. Metadata-backed deployment authorization is the product."

### **1:25–1:40 | One architecture beat**
**On screen (only slide):**

```text
             UNDERWRITE

Deployment ──────► Agent
                    │
                    ▼
                 DataHub
              lineage + tags
                    │
                    ▼
              Policy Boundary
                /        \
             BLOCK      APPROVE
               │
               ▼
            DataHub
           write-back
```

**Say:** "Observe, reason, act, remember — then Assist with Agent Context Kit after a block. The LLM never authorizes."  
Return immediately to product footage.

### **1:40–2:30 | Evidence path + Assist (optional if time)**
**Show:** Evidence path ending at `raw_billing.retention_discount`. Brief remediation beat only if under clock.  
**Say:** "AI explains how to fix it. It cannot override the verdict."

### **2:30–2:50 | Trust the artifact**
**Show:** Pin `freeze-grand-prize-ready`, `examples/sample_outputs/`.  
**Say:** "Judges can inspect a captured live payload without standing up GMS — and reproduce from this tag."

### **2:50–3:00 | Thesis**
**On screen:** Underwrite.  
**Say:** "DataHub knows where your ML features came from. Underwrite makes CI act on that knowledge."

---

## Checklist
- [ ] Recording from `freeze-grand-prize-ready`
- [ ] **Opens on DataHub lineage**, not Underwrite UI / terminal
- [ ] Write-back shown **immediately** after the block (before/after in DataHub)
- [ ] `churn_model_v2` vs `churn_model_v2_fixed` back-to-back
- [ ] One architecture slide only; no stack/DFS narration
- [ ] Agentic sequence: Observe → Reason → Act → Remember → Assist
- [ ] No offline fixture vocabulary
- [ ] Close on the thesis line above
