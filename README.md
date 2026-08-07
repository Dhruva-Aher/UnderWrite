# Underwrite 🛡️

> **Metadata-aware CI that deterministically blocks unsafe ML deployments.**

---

## 🛑 The Problem: Target Leakage is Invisible to CI

A machine learning model cannot unsee data. If forbidden data (like a future outcome) leaks into your training set, the model is corrupted. 

Today, this happens silently. Data is renamed across transformations. Pipelines merge. The leak becomes invisible. You deploy a corrupted model, and it fails catastrophically.

Traditional CI only knows if the code compiles. **It cannot see your metadata.**

---

## 💡 Why It Matters: Actionable Metadata

Underwrite uses metadata to stop bad deployments. It does not just analyze metadata passively—it breaks the build if forbidden data reaches a production model. 

| Feature | GitHub Actions | Underwrite |
| :--- | :---: | :---: |
| Unit Tests & Linting | ✓ | ✓ |
| **Reads Metadata Graph** | ✗ | **✓** |
| **Lineage Traversal (DFS)**| ✗ | **✓** |
| **Blocks Unsafe ML Deployment** | ✗ | **✓** |
| **Writes Incidents back** | ✗ | **✓** |

---

## 🏗️ Architecture: Why Traditional CI Fails

GitHub Actions only sees the *code* that changed. It does not know that a dataset feeds into a pipeline that eventually trains a risk-prediction ML model. 

Underwrite bridges this gap by acting as a strict deployment gate backed by **DataHub**. 

```mermaid
flowchart TD
    subgraph Traditional CI (Blind)
        PR[Deployment Request] --> CodeTest[Unit Tests Pass ✅]
    end

    subgraph Underwrite (Metadata-Aware)
        PR --> DH[(DataHub Fine-Grained Lineage API)]
        DH -- Traverses lineage graph --> Eval[Deterministic Policy Gate]
        Eval -- Violation Found --> Block[❌ Block Build]
        
        Block --> AI[AI Remediation Advisor]
        AI --> Draft[Markdown Remediation Advice]
        Block --> Inc[Write Incident to DataHub]
    end

    CodeTest -.-x Underwrite
    
    classDef safe fill:#2ecc71,stroke:#27ae60,stroke-width:2px,color:white;
    classDef danger fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:white;
    classDef dh fill:#3498db,stroke:#2980b9,stroke-width:2px,color:white;
    
    class CodeTest safe;
    class Block danger;
    class DH dh;
```

**Phase 1: Deterministic Enforcement (Safety)**: We strictly evaluate the column-level fine-grained lineage. Zero heuristics. Zero AI hallucinations. Even an APPROVED payload cannot deploy unless its source is an authoritative live DataHub evaluation.
**Phase 2: Generative Remediation (Velocity)**: **AI-generated remediation runs only when DataHub Agent Context Kit and a configured LLM are available. Otherwise Underwrite returns deterministic evidence-only remediation.**

```python
# Our strict initialization path
tools = build_langchain_tools(
    client,
    include_mutations=False,
)
```

---

## 📸 Product Proof

### 1. The Verification Dashboard
*(See the web UI for live verification results)*

### 2. Live Lineage Visualization
*(Graphs are rendered deterministically from DataHub responses)*

### 3. DataHub Writeback (Incidents)
*(Incidents and tags are synchronized back to DataHub strictly as side effects)*

---

## 🚀 Quick Start

**Supported Environments**: Recommended: Python 3.13. Verified with Python 3.13. (Python 3.14 is currently not supported due to dependency compatibility)

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the orchestrator:
   ```bash
   python demo/run_demo.py
   ```
5. Open the frontend console to see the `reactflow` graph updates.

---

## ❓ FAQ

**Q: Doesn't GitHub Actions already do this?**
A: No. GitHub Actions can execute Underwrite, but ordinary code-level CI cannot determine whether an ML feature is transitively derived from forbidden upstream data. Underwrite uses DataHub's metadata graph to make that authorization decision.

**Q: Why not just use AI to check the PR?**
A: You cannot push an LLM hallucination to a production incident system. We use a deterministic engine for the authorization decision (safety), and AI only for the remediation suggestion (velocity).

---

## 📝 License

Apache 2.0 License.
