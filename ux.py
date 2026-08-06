"""Underwrite — Terminal UX Formatter (ux.py)

Formats InvestigationReport objects into beautiful, readable terminal output.
Highlights the deterministic verification philosophy.
"""

from remediation_engine import InvestigationReport

def format_investigation_report(report: InvestigationReport) -> str:
    """
    Renders the InvestigationReport into a presentation-ready terminal string.
    """
    lines = []
    lines.append("=================================================")
    lines.append("UNDERWRITE AI DATA RELIABILITY ENGINE")
    lines.append("=================================================")
    lines.append("")
    lines.append("The LLM is never trusted. Every proposed fix is treated as a hypothesis")
    lines.append("that must be proven by a deterministic verifier before any action is taken.")
    lines.append("")
    lines.append("Investigation ID")
    lines.append(report.investigation_id)
    lines.append("")
    lines.append("Policy")
    lines.append(report.policy)
    lines.append("")
    lines.append("Status")
    lines.append(report.status)
    lines.append("")
    lines.append("Root Cause")
    lines.append(report.root_cause)
    lines.append("")
    lines.append("Blast Radius")
    lines.append("")
    lines.append(f"Datasets:   {report.blast_radius.datasets}")
    lines.append(f"Models:     {report.blast_radius.models}")
    lines.append(f"Dashboards: {report.blast_radius.dashboards}")
    lines.append("")
    lines.append("Owner")
    lines.append(report.blast_radius.owner)
    lines.append("")
    
    if report.attempts:
        lines.append("Leakage Paths")
        lines.append("")
        lines.append("Before")
        lines.append("")
        # The first attempt's before_count is the total initial evidence
        initial_evidence = report.attempts[0].evidence_count_before
        lines.append(str(initial_evidence))
        lines.append("")
        
        for idx, attempt in enumerate(report.attempts, 1):
            lines.append("↓")
            lines.append("")
            lines.append(f"Attempt {idx}")
            lines.append("")
            lines.append(str(attempt.evidence_count_after))
            lines.append("")
            
            lines.append("-" * 42)
            lines.append("")
            lines.append(f"Attempt {idx}")
            lines.append("")
            lines.append("Patch")
            lines.append(f"File: {attempt.patch.file_path}")
            lines.append(f"Replace: `{attempt.patch.search_text.strip()}` -> `{attempt.patch.replace_text.strip()}`")
            lines.append("")
            lines.append("Verification")
            lines.append("")
            lines.append("PASSED" if attempt.verification_passed else "FAILED")
            lines.append("")
            lines.append("Reason")
            lines.append(attempt.message)
            lines.append("")

    lines.append("-" * 42)
    lines.append("")
    lines.append("Deterministic Policies")
    lines.append("")
    if report.status == "APPROVED":
        lines.append(f"✓ {report.policy}")
    else:
        lines.append(f"❌ {report.policy} (Violated)")
    lines.append("")
    lines.append("Confidence")
    lines.append("")
    lines.append(f"{report.confidence}%")
    lines.append("")
    if report.ready_for_pr:
        lines.append("Ready for GitHub PR")
    else:
        lines.append("Requires Manual Intervention")
    lines.append("")
    lines.append("══════════════════════════════════════")
    lines.append("")
    lines.append("LLM proposed:")
    lines.append(f"{len(report.attempts)} patches")
    lines.append("")
    
    accepted = 1 if report.status == "APPROVED" else 0
    rejected = len(report.attempts) - accepted
    total = len(report.attempts)
    
    lines.append(f"Hypotheses generated       {total}")
    lines.append(f"Hypotheses rejected        {rejected}")
    lines.append(f"Hypotheses accepted        {accepted}")
    lines.append(f"Human decisions automated  0")
    lines.append(f"Human decisions informed   1")
    lines.append("")
    lines.append("Trust the evidence, not the output.")
    lines.append("")
    lines.append("══════════════════════════════════════")
    
    return "\n".join(lines)
