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
  │ 5. Verdict Construction│  Produces structured VerdictInternal & non-blocking write-back
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

## 3. DataHub Write-Back & Invariant 4

**Invariant 4**: Write-back is a pure side effect. Verdict generation and UI rendering **NEVER** depend on write-back success.

When `/evaluate` receives a request:
1. `Agent.evaluate_model()` generates the verdict immediately.
2. The endpoint returns `HTTP 200 OK` payload to the client.
3. Write-back operations (`write_verdict_tag`, `write_incident`, `write_documentation`) are scheduled as non-blocking `BackgroundTasks`.

---

## 4. Configuration Reference

Configuration settings are loaded automatically from environment variables (prefixed with `UNDERWRITE_` or default keys):

| Setting Key | Default Value | Description |
| :--- | :--- | :--- |
| `UNDERWRITE_GMS_URL` | `http://localhost:8080` | DataHub GMS REST API endpoint |
| `UNDERWRITE_HOST` | `127.0.0.1` | Application server host binding |
| `UNDERWRITE_PORT` | `8000` | Application server port |
| `UNDERWRITE_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `UNDERWRITE_POLICY_PATH` | `policies.yaml` | YAML policy definitions filepath |

---

## 5. Testing & Local Development

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
