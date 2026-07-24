# Changelog

All notable changes to Underwrite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-24

### Added
- **5-Stage Decoupled Engine**: Graph Acquisition, Normalization, Traversal, Policy Evaluation, and Verdict Construction (`agent.py`).
- **DataHub Context Platform Integration**: `FineGrainedLineage` GraphQL/REST graph acquisition and bidirectional REST write-backs (`datahub_client.py`).
- **Multi-Policy Framework**: Extensible `PolicyEvaluator` supporting `ML-LEAK-001` (Target Leakage), `ML-TEMPORAL-001`, and `ML-FAIL-CLOSED` rules.
- **Async Telemetry Write-Back**: Non-blocking emissions of `GlobalTags`, `IncidentInfo`, and `InstitutionalMemory` to DataHub GMS.
- **Evidence-First UI & Replay Stepper**: Web application interface featuring step-by-step algorithm replay, lineage graph renderer, and node inspector drawer (`static/`).
- **Layer 0 Offline Fallback**: Embedded fixtures allowing offline presentation without live DataHub Docker dependency.
- **Master Verification Test Runner**: Automated test suite (`test_full_suite.py`) covering unit tests, fail-closed policy checks, and fallback fixtures.
