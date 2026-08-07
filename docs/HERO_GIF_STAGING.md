# Underwrite: Hero GIF Staging Instructions

**Goal:** Create a 10-second, perfectly looping GIF that instantly communicates the core value: "Metadata-aware CI that blocks breaking pull requests."

## Setup Requirements
1. Clean desktop, dark mode IDE (VS Code) open on the left half of the screen.
2. Dark mode GitHub PR page open on the right half.
3. ReactFlow lineage graph pre-loaded in a hidden browser tab (ready to switch to).

## 10-Second Script

**0:00 - 0:02 (The Action)**
- **Visual**: VS Code (left).
- **Action**: Highlight the line `customer_status VARCHAR(50),` in `raw_customers.sql` and hit backspace. 
- **Action**: Type `git commit -m "cleanup"` and hit enter. (Speed up this typing in editing).

**0:02 - 0:05 (The Consequence)**
- **Visual**: GitHub PR page (right).
- **Action**: The PR status checks spinner turns into a red `❌`.
- **Zoom**: Slowly zoom in on the specific Underwrite GitHub Comment that appears:
  > **❌ Blocked: Required Column Removed**
  > `customer_status` is an upstream dependency for 2 ML Models and 11 Dashboards.

**0:05 - 0:10 (The Proof)**
- **Visual**: Switch to the hidden ReactFlow browser tab in full screen.
- **Action**: The graph visually highlights the exact blast radius. The removed node (`customer_status`) pulses red, and the downstream ML model nodes turn red. 
- **Text Overlay** (Optional but recommended in the GIF): "Deterministic lineage traversal powered by DataHub."

## Post-Processing
- Keep the frame rate high (15-24 FPS is better than a choppy 5 FPS GIF).
- Zoom in tight on the GitHub comment text so it is easily readable on a mobile screen.
- Export as `< 5MB` to ensure it loads instantly when judges open the README.
