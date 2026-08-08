# Underwrite: Demo Screenplay (≤ 3 minutes)

**Hard limit**: Judges are not required to watch past three minutes.  
**Thesis (end on this)**: *DataHub already knows how your data is connected. Underwrite makes that knowledge enforceable.*

Do **not** feature-tour. Do **not** equal-bill AI with the gate. Show live DataHub.

---

### **0:00 – 0:20 | Problem**
**Show**: A feature name that looks harmless in training code / a model card.  
**Say**: "This ML feature looks safe in code. Three transformations upstream, it derives from post-outcome data. The model cannot unsee that. Traditional CI never will."

### **0:20 – 0:40 | Why ordinary CI fails**
**Show**: Green unit tests / GitHub checks that only see the repo.  
**Say**: "CI can tell you the code compiles. It cannot tell you whether a feature is transitively derived from forbidden upstream columns. That answer lives in the metadata graph."

### **0:40 – 1:35 | Live DataHub → Underwrite → blocked deploy**
**Show (must be live GMS, not the offline fixture)**:
1. DataHub lineage UI (or seeded graph) for the leak path.
2. `python demo/run_demo.py` (or the API + `deployment_gate.py`) connecting to GMS.
3. **BLOCKED** verdict with evidence path printed.
4. Gate exit non-zero / failed CI check.

**Say**: "Underwrite walks DataHub FineGrainedLineage with a deterministic DFS. Forbidden tag on an upstream field → deployment fails. No LLM in this decision."

### **1:35 – 2:05 | Deterministic evidence / trust boundary**
**Show**: Evidence path list; mention `evaluation_source == live_datahub` required for approve.  
**Say**: "Cached or spoofed 'approved' results cannot pass the gate. DataHub evidence authorizes. AI does not."

### **2:05 – 2:30 | Remediation (supporting)**
**Show**: Remediation markdown from the advisor (ACK, read-only).  
**Say**: "Only after the block does AI explain how to fix the pipeline. It never decides whether deploy succeeds."

### **2:30 – 2:50 | DataHub writeback**
**Show**: Incident / tag written back in DataHub UI for the blocked model.  
**Say**: "Authorization and catalog mutation are separate. Writeback failure does not rewrite the verdict."

### **2:50 – 3:00 | Thesis**
**On screen**: Underwrite.  
**Say**: "DataHub already knows how your data is connected. Underwrite makes that knowledge enforceable."

---

## Recording checklist

- [ ] GMS running; `python seed.py` completed before recording
- [ ] Demo banner / logs say **LIVE DataHub**, never mock-as-real
- [ ] No sqlglot / AST / "column drop blast radius" narrative — product is **lineage → policy → CI exit**
- [ ] AI appears after the block, not as co-equal headline
