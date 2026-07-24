# Contributing to Underwrite

Thank you for your interest in contributing to Underwrite! Underwrite is an open-source ML governance intercept agent built on DataHub's Context Platform.

---

## Code of Conduct
We are committed to providing a welcoming and inclusive community. Please be respectful and constructive in all communications.

---

## Development Setup

### 1. Prerequisites
- Python 3.12
- Docker Desktop (for running DataHub GMS locally)

### 2. Obtain the source
Clone or download this repository, then change into its root directory.

### 3. Environment Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Running Tests
Run the master test runner verifying graph acquisition, traversal, and fail-closed policies:
```bash
python test_full_suite.py
```

---

## Architecture Guidelines
- **Deterministic Enforcement**: All policy graph traversal logic must remain 100% deterministic inside `agent.py`.
- **Decoupled Engine**: Graph traversal must operate strictly on in-memory `InternalGraph` instances and never make SDK calls during search.
- **Async Write-Back**: DataHub write-backs in `datahub_client.py` must run as non-blocking side effects.

---

## Submitting Pull Requests
1. Create a feature branch: `git checkout -b feature/my-new-policy`
2. Ensure all tests pass: `python test_full_suite.py`
3. Commit with concise messages following Conventional Commits format.
4. Open a Pull Request on GitHub.

---

## License
By contributing, you agree that your contributions will be licensed under the [Apache License, Version 2.0](LICENSE).
