# Underwrite: Demo Screenplay

**Target Runtime**: 2 minutes 30 seconds.
**Goal**: Design the judge's emotional journey. Move them from realizing the severity of the problem to trusting the deterministic solution, to being wowed by the AI remediation.

---

### **0:00 – 0:15 | The Hook**
**Knowledge**: CI misses metadata failures (Target Leakage).
**Feeling**: *"Oh... that's actually a massive blind spot."*
**Visual**: Fast-paced B-roll of standard GitHub Actions passing (green checks), hard-cutting to a chaotic dashboard with missing data and a corrupted ML model accuracy graph plummeting.
**Voiceover**: "Every day, engineers merge pull requests that pass all unit tests, but silently destroy downstream machine learning models through target leakage. Traditional CI only knows if code compiles. It cannot see your metadata."

### **0:15 – 0:30 | The Action**
**Knowledge**: It happens easily in everyday development.
**Feeling**: *"I can see myself or my team making this exact mistake."*
**Visual**: Screen recording of VS Code. We see "Alice" (a developer) confidently delete a seemingly unused column `customer_status` from a dbt model and push the PR. 
**Voiceover**: "Watch Alice. She's cleaning up a dbt model and drops a column she thinks is obsolete. She pushes the PR, expecting it to merge."

### **0:30 – 0:45 | The Interception**
**Knowledge**: Underwrite breaks the build safely and clearly.
**Feeling**: *"Wow, that caught it immediately."*
**Visual**: GitHub PR page. The Underwrite check turns red. We ZOOM IN on the automated comment: `❌ Blocked: customer_status breaks 2 ML Models`.
**Voiceover**: "But Underwrite intercepts the deployment. In less than 100 milliseconds, it computes the semantic SQL delta and blocks the merge."

### **0:45 – 1:00 | The Proof (Deterministic Traversal)**
**Knowledge**: It uses DataHub lineage, not just string matching.
**Feeling**: *"This is deeply technical and trustworthy."*
**Visual**: Cut to the Underwrite ReactFlow UI. The screen shows the exact cycle-safe DFS traversal across the DataHub lineage graph. The node Alice dropped pulses red, sending a shockwave down to the ML models.
**Voiceover**: "How? Underwrite queries DataHub's real-time Fine-Grained Lineage API. It performs a deterministic, mathematical traversal of the graph. Zero heuristics. Zero hallucinations. Just hard facts."

### **1:00 – 1:15 | The "Human-in-the-Loop" Trust**
**Knowledge**: The deterministic engine and the AI are separate. 
**Feeling**: *"They understand enterprise security. This isn't just a GPT wrapper."*
**Visual**: UI focuses on the "Audit Trail" panel. It shows the raw API JSON response from DataHub, clearly marked `Deterministic Gate: FAILED`.
**Voiceover**: "Because we are operating at the deployment gate, we cannot rely on LLMs to make authorization decisions. The deterministic engine is the absolute authority."

### **1:15 – 1:45 | The Remediation (AI Velocity)**
**Knowledge**: AI is used to fix the problem *after* the gate fails.
**Feeling**: *"That is incredibly useful for developer velocity."*
**Visual**: We pan over to the "AI Remediation Advisor" panel in the UI. It generates a LangChain investigation, queries DataHub for alternative columns, and proposes a fix.
**Voiceover**: "But we still want developer velocity. Once the build is safely blocked, our read-only AI agent investigates the DataHub metadata. It finds that `customer_status_v2` is the approved alternative and drafts a PR comment with the exact code to fix the pipeline."

### **1:45 – 2:00 | The Writeback (Actionable Metadata)**
**Knowledge**: Underwrite treats DataHub as an operational brain.
**Feeling**: *"This is the perfect sponsor integration."*
**Visual**: The DataHub UI. We see a new "Incident" automatically created on the affected ML model, reading: `At-Risk: Upstream PR #104 pending`.
**Voiceover**: "Finally, we make metadata actionable. Underwrite writes an Incident directly back into DataHub, alerting data scientists that their model is currently under threat from an active PR."

### **2:00 – 2:15 | The Realization**
**Knowledge**: This scales to any enterprise stack.
**Feeling**: *"This is a billion-dollar SaaS product, not a hack."*
**Visual**: A polished, linear-style architecture diagram fading in, contrasting "Traditional CI" with "Underwrite CI". 
**Voiceover**: "By combining deterministic safety with AI-driven remediation, Underwrite guarantees that corrupted data never reaches production."

### **2:15 – 2:30 | The Outro**
**Knowledge**: The memory anchor.
**Feeling**: *"I will remember this project tomorrow."*
**Visual**: The Hero GIF looping in the center of the screen. Text on screen: "Underwrite."
**Voiceover**: "Underwrite. Metadata-aware CI that blocks breaking pull requests."
