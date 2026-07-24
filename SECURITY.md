# Security Policy

## Reporting Security Vulnerabilities

The Underwrite team takes security seriously. If you discover a security vulnerability in Underwrite, please do NOT create a public issue.

Instead, please send a security report to **security@datahubproject.io**.

### What to include in your report:
- A description of the vulnerability and potential impact.
- Steps to reproduce the issue.
- Proof of concept code or payload (if applicable).

We will acknowledge receipt of your report within 48 hours and work with you to remediate the vulnerability.

---

## Security Model & Policy Boundaries

Underwrite operates as a CI/CD deployment gate sentinel:
- **Fail-Closed Governance**: Missing, broken, or unresolvable lineage provenance automatically triggers a `blocked` verdict (`INCOMPLETE_LINEAGE`).
- **Read-Only Context Traversal**: Graph traversal operates strictly in-memory without mutating source databases.
- **Idempotent Write-Back**: DataHub GMS REST emissions write global tags and dataset incidents via idempotent URNs.
