"""Fail-closed deployment gate for CI/CD systems with rich compiler-style diagnostics.

Usage:
    python scripts/deployment_gate.py --model-urn 'urn:li:mlModel:(...)'

The process exits 0 only for a live DataHub-backed approved evaluation.
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.parse

import httpx

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
GRAY = "\033[90m"


def dataset_urn_from_schema_field(urn: str) -> str:
    """Unwrap the parent dataset URN from a schemaField URN.

    A schemaField URN embeds the whole dataset URN, which itself contains commas,
    so only the final comma separates the dataset from the field path.
    """
    prefix = "urn:li:schemaField:("
    if urn.startswith(prefix) and urn.endswith(")"):
        inner = urn[len(prefix) : -1]
        if "," in inner:
            return inner.rsplit(",", 1)[0]
    return urn


def datahub_entity_url(urn: str) -> str:
    """Build a browsable DataHub UI link for an entity URN."""
    base = os.getenv("UNDERWRITE_DATAHUB_UI_URL", "http://localhost:9002").rstrip("/")
    kind = "dataset" if urn.startswith("urn:li:dataset:") else "entity"
    return f"{base}/{kind}/{urllib.parse.quote(urn, safe='')}"


def default_principal() -> str:
    """Identify the CI actor requesting the deployment, for the audit trail."""
    actor = (
        os.getenv("UNDERWRITE_REQUESTED_BY")
        or os.getenv("GITHUB_ACTOR")
        or os.getenv("GITLAB_USER_LOGIN")
        or os.getenv("BUILD_REQUESTEDFOR")
        or os.getenv("USER")
    )
    if not actor:
        return "urn:li:corpuser:ci-deployment-gate"
    if actor.startswith("urn:li:corpuser:"):
        return actor
    return f"urn:li:corpuser:{actor}"


def set_github_output(name: str, value: str):
    """Write an output variable to the GitHub Actions output file."""
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{name}={value}\n")


def print_diagnostic(label: str, value: str, color: str = ""):
    """Print a Cargo/Terraform-style diagnostic line."""
    print(f"  {BOLD}{label.rjust(14)}:{RESET} {color}{value}{RESET}")


def process_payload(api_url: str, payload: dict) -> int:
    """Translate an Underwrite evaluation payload into a CI-safe exit code."""
    req = payload.get("request", {})
    evl = payload.get("evaluation", {})
    source = payload.get("evaluation_source", "unknown")
    verdict = evl.get("verdict", "blocked")
    reason_code = evl.get("reason_code", "UNKNOWN_ERROR")
    latency = evl.get("latency_ms", 0)
    decision_id = req.get("request_id", "UNKNOWN")
    evidence_paths = payload.get("evidence_paths", [])
    remediation_available = payload.get("remediation_available", False)
    timeout_seconds = 15.0

    set_github_output("verdict", verdict)
    set_github_output("decision_id", decision_id)
    set_github_output("reason_code", reason_code)
    set_github_output("latency_ms", str(latency))
    set_github_output("evaluation_source", source)

    if source != "live_datahub":
        print(f"{BOLD}{RED}error:{RESET} {reason_code}")
        print_diagnostic("Exit Reason", "Evaluation is not backed by live DataHub evidence.")
        print_diagnostic("Source", source, YELLOW)
        print("\n::error title=Underwrite Verification Failed::Live DataHub evidence required.")
        return 1

    if verdict == "approved":
        print(f"{BOLD}{GREEN}success:{RESET} {reason_code}")
        print_diagnostic("Policy", "All deterministic checks passed")
        print_diagnostic("Decision", "APPROVED", GREEN)
        print_diagnostic("Decision ID", decision_id)
        print_diagnostic("Latency", f"{latency}ms")
        print_diagnostic("Next Action", "Proceed with deployment")
        return 0

    print(f"{BOLD}{RED}error:{RESET} {reason_code}")
    print_diagnostic("Decision", "BLOCKED", RED)
    print_diagnostic("Policy", reason_code)

    evidence_str = "No specific evidence path provided."
    if evidence_paths:
        ep = evidence_paths[0]
        tainted_urn = ep.get("tainted_urn", "unknown")
        feature_urn = ep.get("feature_urn", "unknown")
        tag = ep.get("tag_found", "unknown")
        evidence_str = f"Feature {feature_urn} derives from forbidden upstream {tainted_urn} (Tag: {tag})"

        if tainted_urn != "unknown":
            dataset_urn = dataset_urn_from_schema_field(tainted_urn)
            print_diagnostic("DataHub Ref", dataset_urn)
            print_diagnostic("DataHub URL", datahub_entity_url(dataset_urn), CYAN)

    print_diagnostic("Evidence", evidence_str)
    print_diagnostic("Decision ID", decision_id)
    print_diagnostic("Latency", f"{latency}ms")
    print_diagnostic("Next Action", "Deployment terminated. Inspect DataHub graph for lineage violation.")
    print()

    if remediation_available and evidence_paths:
        try:
            rem_endpoint = f"{api_url.rstrip('/')}/remediation/{decision_id}"
            with httpx.Client(timeout=timeout_seconds) as client:
                rem_resp = client.post(rem_endpoint)
            rem_resp.raise_for_status()
            rem_payload = rem_resp.json()
            markdown = rem_payload.get("markdown", "")
            print(f"{BOLD}Remediation Advisor:{RESET}")
            for line in markdown.splitlines():
                print(f"  {line}")
            print()
        except Exception as e:
            print(f"  {GRAY}Remediation Advisor unavailable: {e}{RESET}\n")

    print(f"::error title=Underwrite: {reason_code}::Deployment blocked. {evidence_str}")
    return 1


def evaluate_deployment(
    api_url: str,
    model_urn: str,
    timeout_seconds: float,
    requested_by: str | None = None,
) -> int:
    """Call Underwrite and translate its result into a CI-safe decision with rich output."""
    endpoint = f"{api_url.rstrip('/')}/evaluate"
    requested_by = requested_by or default_principal()

    print(f"\n{BOLD}{CYAN}Underwrite ━━ Executable Metadata{RESET}")
    print(f"{GRAY}Evaluating deployment against DataHub graph...{RESET}\n")

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                endpoint, json={"model_urn": model_urn, "requested_by": requested_by}
            )
        response.raise_for_status()
        payload = response.json()
    except (httpx.RequestError, ValueError) as exc:
        print(f"{BOLD}{RED}error:{RESET} Failed to reach Underwrite API at {endpoint}")
        print(f"  {GRAY}{exc}{RESET}")
        print(f"::error title=Underwrite API Error::Failed to reach Underwrite API: {exc}")
        return 1
    except httpx.HTTPStatusError as exc:
        print(f"{BOLD}{RED}error:{RESET} API returned status {exc.response.status_code}")
        print(f"  Response: {exc.response.text}")
        return 1

    return process_payload(api_url, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed Underwrite deployment gate")
    parser.add_argument("--model-urn", required=True)
    parser.add_argument(
        "--api-url", default=os.getenv("UNDERWRITE_API_URL", "http://127.0.0.1:8000")
    )
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    parser.add_argument("--requested-by", default=default_principal())
    args = parser.parse_args()

    print("::group::Underwrite Evaluation")
    exit_code = evaluate_deployment(
        args.api_url, args.model_urn, args.timeout_seconds, args.requested_by
    )
    print("::endgroup::")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
