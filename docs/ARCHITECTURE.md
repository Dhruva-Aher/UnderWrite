# Underwrite — System Architecture & Metadata Specification

## Overview

**Underwrite** is an automated AI governance and lineage inspection platform designed to prevent untrusted or leaky ML models from reaching production. It inspects DataHub metadata graphs, evaluates policy rules, and records audit verdicts as non-blocking side effects.

---

## 1. 5-Stage Core Detection Pipeline

```
  ┌────────────────────────┐
  │ 1. Graph Acquisition   │  Fetches raw ML model & dataset aspects via MetadataClient
  └───────────┬────────────┘
              │
  ┌───────────▼────────────┐
  │ 2. Graph Normalization │  Converts raw aspects into an in-memory InternalGraph
  └───────────┬────────────┘
              │
  ┌───────────▼────────────┐
  │ 3. Graph Traversal     │  Performs pure in-memory DFS walk (0 SDK calls)
  └───────────┬────────────┘
              │
  ┌───────────▼────────────┐
  │ 4. Rule Evaluation     │  Evaluates Policy rules (e.g. Target Leakage, Incomplete Lineage)
  └───────────┬────────────┘
              │
  ┌───────────▼────────────┐
  │ 5. Verdict Construction│  Produces VerdictInternal & requested DataHub metadata mutations
  └────────────────────────┘
```

---

## 2. Component Boundaries & Domain Subsystems

- **`config.py`**: Centralized configuration management using Pydantic `BaseSettings` (`gms_url`, `host`, `port`, `log_level`, `policy_path`).
- **`exceptions.py`**: Typed domain exception hierarchy (`UnderwriteError`, `DataHubError`, `NetworkError`, `AuthenticationError`, `ValidationError`, `SchemaError`).
- **`metadata/`**: Domain-driven metadata module:
  - `client.py`: `MetadataClient(Protocol)` interface, `DataHubClient` (SDK wrapper), and `MockMetadataClient` (in-memory zero-network testing).
  - `urns.py`: Standardized URN builders (`make_ml_model_urn`, `make_dataset_urn`, `make_tag_urn`) and pre-defined domain constants.
  - `aspects.py`: Metadata Change Proposal (MCP) builders for tags, operational incidents, and institutional memory documentation.
- **`agent.py`**: Core detection engine using explicit constructor Dependency Injection (`Agent(client, settings, logger)`).
- **`app.py`**: Event-driven FastAPI web server exposing `/evaluate`, `/override`, and `/health` endpoints.
- **`tests/`**: Isolated test suite:
  - `tests/unit/`: Pure unit tests executed in **< 1s with 0 external network dependencies**.
  - `tests/integration/`: Live DataHub GMS tests with graceful `pytest.skip()` auto-detection when GMS is offline.

---

## 3. Requested DataHub Metadata Mutations & Invariant 4

**Invariant 4**: A requested DataHub metadata mutation is a pure side effect. Verdict generation and UI rendering **NEVER** depend on mutation confirmation.

When `/evaluate` receives a request:
1. `Agent.evaluate_model()` generates the verdict immediately.
2. The endpoint returns `HTTP 200 OK` payload to the client.
3. DataHub metadata mutation requests (`write_verdict_tag`, `write_incident`, `write_documentation`) are scheduled as non-blocking `BackgroundTasks`.

DataHub metadata mutation requests are scheduled only when `evaluation_source` is `live_datahub`.
Bundled cached fixtures are deliberately excluded: a fixture must never mutate
an enterprise metadata catalog.

## 4. Deployment Enforcement Boundary

The service returns a governance decision; the bundled
[`scripts/deployment_gate.py`](scripts/deployment_gate.py) is the fail-closed
caller used by CI/CD. It exits successfully only when `/evaluate` returns both
`verdict: approved` and `evaluation_source: live_datahub`. This makes the
deployment boundary executable rather than a documentation convention.

`/override` records a token-authenticated override statement in DataHub for audit
purposes. It does not alter the evaluation verdict, decision store, or deployment
gate exit code. The endpoint is disabled unless `UNDERWRITE_OVERRIDE_TOKEN` is
configured, and requires that value in the `X-Underwrite-Override-Token` header.

---

## 5. Configuration Reference

Configuration settings are loaded automatically from environment variables (prefixed with `UNDERWRITE_` or default keys):

| Setting Key | Default Value | Description |
| :--- | :--- | :--- |
| `UNDERWRITE_GMS_URL` | `http://localhost:8080` | DataHub GMS REST API endpoint |
| `UNDERWRITE_HOST` | `127.0.0.1` | Application server host binding |
| `UNDERWRITE_PORT` | `8000` | Application server port |
| `UNDERWRITE_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `UNDERWRITE_POLICY_PATH` | `policies.yaml` | YAML policy definitions filepath |
| `UNDERWRITE_OVERRIDE_TOKEN` | unset (disabled) | Required secret for `/override` audit writes |

---

## 6. Testing & Local Development

### Run Unit Test Suite (100% Offline, Zero Network Calls)
```bash
pytest tests/unit
```

### Run Integration Test Suite (Auto-skips if DataHub GMS is offline)
```bash
pytest tests/integration
```

### Run Full Master Suite
```bash
python test_full_suite.py
```

### Launch Preflight Verification & App Server
```bash
python preflight.py
```
