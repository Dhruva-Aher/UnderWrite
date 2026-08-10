# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in UnderWrite, please do **not** open a public issue with exploit details.

Report it privately via [GitHub Security Advisories](https://github.com/Dhruva-Aher/UnderWrite/security/advisories/new) for this repository.

### What to include in your report
- A description of the vulnerability and potential impact
- Steps to reproduce the issue
- Proof of concept code or payload (if applicable)

This project is independently maintained. Do **not** send UnderWrite vulnerability reports to DataHub project security contacts unless the issue is in upstream DataHub itself.

---

## Security Model & Policy Boundaries

UnderWrite operates as a CI/CD deployment gate:

- **Fail-closed governance**: Missing, broken, or unresolvable lineage provenance triggers a `blocked` verdict (`INCOMPLETE_LINEAGE`).
- **Read-only context traversal**: Graph traversal operates in-memory without mutating source systems during evaluation.
- **Idempotent write-back**: DataHub GMS emissions write global tags and dataset incidents via deterministic URNs. Write-back never mutates the verdict.
