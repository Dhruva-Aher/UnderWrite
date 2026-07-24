# Underwrite — Marketing & Presentation Asset Index

This directory contains crisp, Retina-resolution (2x scale factor, 1440x900 dark mode) screenshot assets for **Underwrite — ML Governance Console**.

---

## Asset Directory

### 1. `01-hero.png`
- **Purpose**: Introduce the core product interface in its baseline ready state.
- **Visible Elements**: Header status badge, model selector, primary `Evaluate deployment` button, and initial layout.
- **Recommended Usage**: Primary GitHub README Hero Image, Devpost Card Thumbnail, Website Header.

### 2. `02-blocked.png`
- **Purpose**: Demonstrate immediate visual feedback for a blocked deployment due to structural target leakage.
- **Visible Elements**: Prominent `BLOCKED` status hero card, reason code, cached-fixture source label, traversal metadata, and evidence rationale.
- **Recommended Usage**: README Problem/Solution Section, Devpost Key Feature Showcase, Slide Presentations.

### 3. `03-lineage.png`
- **Purpose**: Highlight the signature interactive column-level lineage graph visualization.
- **Visible Elements**: SVG fixture lineage DAG, node type legend toolbar, and selected-node provenance inspector.
- **Recommended Usage**: Project Signature Asset, GitHub Banner, Product Demo Slides, Technical Deep Dive Documentation.

### 4. `04-replay.png`
- **Purpose**: Explain how the deterministic detection engine works step-by-step.
- **Visible Elements**: Expanded Execution Pipeline panel. Cached fixtures may show that no live execution trace is available.
- **Recommended Usage**: Technical Architecture Documentation, How-It-Works README section, Judge Presentation Slides.

### 5. `05-writeback.png`
- **Purpose**: Show the write-back panel state associated with a verdict.
- **Visible Elements**: Expanded DataHub Write-Back panel. Cached fixtures do not claim a live write-back request.
- **Recommended Usage**: Integrations & DataHub Section, Governance Audit Trail Showcase, Devpost Feature Grid.

### 6. `06-approved.png`
- **Purpose**: Show a successful, clean deployment evaluation create a complete before/after story.
- **Visible Elements**: Emerald green `APPROVED` status hero card, checkmark icon, `churn_model_v2_fixed`, and bundled-fixture source label.
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
