# Architectural Tradeoffs

This document outlines the deliberate architectural tradeoffs made in Underwrite. It exists to clarify that these decisions are intentional engineering choices optimizing for the hackathon constraints and deployment gate use case, rather than missing features.

## 1. Client-Side In-Memory Graph Traversal
- **Decision**: Lineage graphs are fetched via REST and traversed in-memory on the client using a cycle-safe DFS.
- **Why it was chosen**: Enables rapid prototyping of complex, deterministic policy rules that require tracking path history, which is difficult to express natively in GraphQL or Neo4j.
- **Alternative considered**: Executing lineage traversal directly within DataHub's backend or GraphQL layer.
- **Why the alternative was rejected**: Pushing complex policy logic into the database requires custom plugins and DataHub core modifications, slowing iteration speed.
- **Hackathon rationale**: Prioritizes shipping the policy engine and proving the business value without modifying DataHub core.
- **Production evolution path**: Push execution down to DataHub's Graph Service via a native plugin to scale across enterprise graphs with millions of nodes.

## 2. Decoupled Metadata Mutations (Eventual Durability)
- **Decision**: DataHub metadata writes (Tags, Incidents) are executed as non-blocking background tasks after the deployment gate returns a verdict.
- **Why it was chosen**: Prevents CI/CD pipelines from hanging if the DataHub API is slow, keeping deployments fast.
- **Alternative considered**: Synchronous metadata writes before returning the HTTP 200 response, or durable Kafka ingestion.
- **Why the alternative was rejected**: Synchronous writes add latency and couple CI/CD reliability to DataHub's write availability.
- **Hackathon rationale**: Demonstrates side-effect mutations while maintaining the invariant that the deployment gate is blazing fast.
- **Production evolution path**: Implement a durable outbox pattern or publish mutations directly to DataHub's Kafka ingestion topic to prevent silent telemetry loss on pod crash.

## 3. Synchronous CI/CD Interception
- **Decision**: The deployment gate intercepts the CI/CD pipeline synchronously via a REST API.
- **Why it was chosen**: A deployment gate must physically break the build before a corrupted model reaches production.
- **Alternative considered**: Triggering governance checks asynchronously via DataHub Actions on the MCL stream.
- **Why the alternative was rejected**: Asynchronous alerting occurs after the fact. By the time an MCL event is processed, the model has already been deployed.
- **Hackathon rationale**: Proves that DataHub metadata can actively prevent incidents in real-time, moving beyond passive alerting.
- **Production evolution path**: Maintain the synchronous gate for deployments, while packaging the evaluation engine as a DataHub Action for continuous, asynchronous monitoring.

## 4. Strict Fine-Grained Lineage Evaluation
- **Decision**: The engine strictly evaluates column-level fine-grained lineage and ignores coarse-grained dataset-to-dataset lineage.
- **Why it was chosen**: Provides surgical precision. A restricted column should not block safe features derived from other columns in the same dataset.
- **Alternative considered**: Falling back to coarse-grained lineage if fine-grained mapping is missing.
- **Why the alternative was rejected**: Coarse-grained evaluation causes unacceptable false positives, blocking safe pipelines and causing alert fatigue.
- **Hackathon rationale**: Demonstrates the precise analytical power of column-level lineage over legacy table-level checks.
- **Production evolution path**: Implement a configurable strictness mode allowing evaluation to fall back to coarse-grained lineage, accompanied by UI warnings about potential false positives.

## 5. Static Override Token
- **Decision**: `/override` records a named human override statement in DataHub when a static token is supplied via HTTP header. It does not alter the deterministic verdict or deployment-gate exit code.
- **Why it was chosen**: Allows a simple, stateless mechanism to demonstrate auditable human acknowledgment without expanding authorization surface area.
- **Alternative considered**: Authenticating the override request against DataHub's native Role-Based Access Control (RBAC), or making `/override` change the gate verdict.
- **Why the alternative was rejected**: Full RBAC requires complex DataHub Access Policies and PATs that complicate local judging. Changing the gate verdict would expand security-sensitive authorization behavior beyond what this demo needs.
- **Hackathon rationale**: Demonstrates auditable override statements without friction during demo setup, while keeping the deployment gate fail-closed and independent.
- **Production evolution path**: Authenticate override requests using DataHub PATs, evaluate permissions against native DataHub Access Policies, and (if required) implement a separate, explicitly authorized bypass path that the gate consults.
