# Underwrite — Marketing & Presentation Asset Index

This directory contains crisp, Retina-resolution (2x scale factor, 1440x900 dark mode) screenshot assets for **Underwrite — ML Governance Console**.

---

## Asset Directory

### 1. `01-hero.png`
- **Purpose**: Introduce the core product interface in its baseline ready state.
- **Visible Elements**: Header with live status badge, model deployment selector, primary `Evaluate & Deploy` CTA button, clean initial layout.
- **Recommended Usage**: Primary GitHub README Hero Image, Devpost Card Thumbnail, Website Header.

### 2. `02-blocked.png`
- **Purpose**: Demonstrate immediate visual feedback for a blocked deployment due to structural target leakage.
- **Visible Elements**: Prominent `BLOCKED` status hero card, shield icon, policy rule ID (`ML-LEAK-001`), traversal metadata, and evidence rationale.
- **Recommended Usage**: README Problem/Solution Section, Devpost Key Feature Showcase, Slide Presentations.

### 3. `03-lineage.png`
- **Purpose**: Highlight the signature interactive column-level lineage graph visualization.
- **Visible Elements**: SVG lineage DAG, node type visual legend toolbar, clicked `raw_billing` tainted node with active upstream/downstream path highlighting and dimmed unrelated nodes.
- **Recommended Usage**: Project Signature Asset, GitHub Banner, Product Demo Slides, Technical Deep Dive Documentation.

### 4. `04-replay.png`
- **Purpose**: Explain how the deterministic detection engine works step-by-step.
- **Visible Elements**: Expanded Execution Pipeline section with vertical timeline tracing Acquisition, Normalization, Traversal walk, Policy Matching, and DataHub Persistence.
- **Recommended Usage**: Technical Architecture Documentation, How-It-Works README section, Judge Presentation Slides.

### 5. `05-writeback.png`
- **Purpose**: Demonstrate that deployment verdicts and audit trails are persisted back to DataHub.
- **Visible Elements**: Expanded DataHub Write-Back panel showcasing explicit aspect badges (`GlobalTags`, `IncidentInfo`, `InstitutionalMemory`) and emission status flags.
- **Recommended Usage**: Integrations & DataHub Section, Governance Audit Trail Showcase, Devpost Feature Grid.

### 6. `06-approved.png`
- **Purpose**: Show a successful, clean deployment evaluation create a complete before/after story.
- **Visible Elements**: Emerald green `APPROVED` status hero card, checkmark icon, clean lineage indication (`churn_model_v2_fixed`), and queued write-back status.
- **Recommended Usage**: Before/After Comparisons, Product Walkthrough Gallery, Success Case Presentation Slide.

### 7. `07-offline.png`
- **Purpose**: Demonstrate system resilience and graceful degradation under offline/cached conditions.
- **Visible Elements**: Amber `DataHub: Cached Mode` connection status pill, highlighting fallback fixture operations when DataHub GMS is offline.
- **Recommended Usage**: System Architecture Documentation, Reliability & Fault-Tolerance Showcase.

---

## Technical Specifications

- **Format**: PNG (Portable Network Graphics)
- **Viewport Dimension**: 1440 × 900 px
- **Pixel Density**: 2.0x (Retina)
- **Color Scheme**: Dark Mode (`--surface-0` `#08090d` base palette)
- **Generation Script**: [`capture_screenshots.py`](../capture_screenshots.py)
- **Prerequisite**: Run `python -m playwright install chromium` after installing `requirements.txt`.
