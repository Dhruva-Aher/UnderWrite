"""Fail-closed deployment gate for CI/CD systems with rich compiler-style diagnostics.

Usage:
    python scripts/deployment_gate.py --model-urn 'urn:li:mlModel:(...)'

The process exits 0 only for a live DataHub-backed approved evaluation.
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
GRAY = "\033[90m"


def set_github_output(name: str, value: str):
    """Write an output variable to the GitHub Actions output file."""
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{name}={value}\n")


def print_diagnostic(label: str, value: str, color: str = ""):
    """Print a Cargo/Terraform-style diagnostic line."""
    print(f"  {BOLD}{label.rjust(14)}:{RESET} {color}{value}{RESET}")


def evaluate_deployment(api_url: str, model_urn: str, timeout_seconds: float) -> int:
    """Call Underwrite and translate its result into a CI-safe decision with rich output."""
    endpoint = f"{api_url.rstrip('/')}/evaluate"
    
    print(f"\n{BOLD}{CYAN}Underwrite ━━ Executable Metadata{RESET}")
    print(f"{GRAY}Evaluating deployment against DataHub graph...{RESET}\n")
    
    # 1. Fetch payload
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(endpoint, json={"model_urn": model_urn})
        response.raise_for_status()
        payload = response.json()
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
        print(f"{BOLD}{RED}error:{RESET} Failed to reach Underwrite API at {endpoint}")
        print(f"  {GRAY}{exc}{RESET}")
        print(f"::error title=Underwrite API Error::Failed to reach Underwrite API: {exc}")
        return 1

    # 2. Extract fields
    req = payload.get("request", {})
    evl = payload.get("evaluation", {})
    source = payload.get("evaluation_source", "unknown")
    verdict = evl.get("verdict", "blocked")
    reason_code = evl.get("reason_code", "UNKNOWN_ERROR")
    latency = evl.get("latency_ms", 0)
    decision_id = req.get("request_id", "UNKNOWN")
    evidence_paths = payload.get("evidence_paths", [])
    remediation_available = payload.get("remediation_available", False)

    # Write Outputs
    set_github_output("verdict", verdict)
    set_github_output("decision_id", decision_id)
    set_github_output("reason_code", reason_code)
    set_github_output("latency_ms", str(latency))
    set_github_output("evaluation_source", source)

    # 3. Validation Rules
    if source != "live_datahub":
        print(f"{BOLD}{RED}error:{RESET} {reason_code}")
        print_diagnostic("Exit Reason", "Evaluation is not backed by live DataHub evidence.")
        print_diagnostic("Source", source, YELLOW)
        print("\n::error title=Underwrite Verification Failed::Live DataHub evidence required. Received cached fallback.")
        return 1

    # 4. Rich Diagnostic Output
    if verdict == "approved":
        print(f"{BOLD}{GREEN}success:{RESET} {reason_code}")
        print_diagnostic("Policy", "All deterministic checks passed")
        print_diagnostic("Decision", "APPROVED", GREEN)
        print_diagnostic("Decision ID", decision_id)
        print_diagnostic("Latency", f"{latency}ms")
        print_diagnostic("Next Action", "Proceed with deployment")
        return 0

    # Blocked formatting
    print(f"{BOLD}{RED}error:{RESET} {reason_code}")
    print_diagnostic("Decision", "BLOCKED", RED)
    print_diagnostic("Policy", reason_code)
    
    evidence_str = "No specific evidence path provided."
    if evidence_paths:
        ep = evidence_paths[0]
        tainted_urn = ep.get("tainted_urn", "unknown")
        feature_urn = ep.get("feature_urn", "unknown")
        tag = ep.get("tag_found", "unknown")
        evidence_str = f"Feature {feature_urn} derives from forbidden dataset {tainted_urn} (Tag: {tag})"
        
        # Link back to DataHub
        dataset_name = tainted_urn.split(",")[-2] if "," in tainted_urn else tainted_urn
        print_diagnostic("DataHub Ref", f"{req.get('gms_endpoint', 'http://localhost:8080')}/dataset/{dataset_name}")

    print_diagnostic("Evidence", evidence_str)
    print_diagnostic("Decision ID", decision_id)
    print_diagnostic("Latency", f"{latency}ms")
    print_diagnostic("Next Action", "Deployment terminated. Inspect DataHub graph for lineage violation.")
    print()

    if remediation_available and evidence_paths:
        try:
            rem_endpoint = f"{api_url.rstrip('/')}/remediation/{decision_id}"
            with httpx.Client(timeout=timeout_seconds) as client:
                rem_resp = client.post(rem_endpoint, json={
                    "model_urn": model_urn,
                    "evidence_path": evidence_paths[0],
                    "policy_id": evidence_paths[0].get("policy_id", reason_code)
                })
            rem_resp.raise_for_status()
            rem_payload = rem_resp.json()
            
            print(f"{GRAY}{rem_payload.get('disclaimer_banner', '')}{RESET}\n")
            print(f"{BOLD}Root Cause:{RESET}\n{rem_payload.get('root_cause')}\n")
            print(f"{BOLD}Evidence Confidence:{RESET}\n{rem_payload.get('evidence_confidence')}\n")
            
            files = rem_payload.get('files_to_inspect', [])
            if files:
                print(f"{BOLD}Files to inspect:{RESET}")
                for f in files:
                    print(f"  - {f}")
                print()
                
            print(f"{BOLD}Suggested Investigation:{RESET}\n{rem_payload.get('suggested_investigation')}\n")
            
            print(f"{BOLD}Potential Patch:{RESET}")
            for line in rem_payload.get("potential_patch", "").splitlines():
                print(f"  {line}")
            print()
            
        except Exception as e:
            print(f"  {GRAY}Remediation Advisor unavailable: {e}{RESET}\n")

    # GitHub Annotation
    print(f"::error title=Underwrite: {reason_code}::Deployment blocked. {evidence_str}")
    
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed Underwrite deployment gate")
    parser.add_argument("--model-urn", required=True)
    parser.add_argument(
        "--api-url", default=os.getenv("UNDERWRITE_API_URL", "http://127.0.0.1:8000")
    )
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    args = parser.parse_args()
    
    print("::group::Underwrite Evaluation")
    exit_code = evaluate_deployment(args.api_url, args.model_urn, args.timeout_seconds)
    print("::endgroup::")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
