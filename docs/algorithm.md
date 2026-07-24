# Underwrite — Structural Target Leakage & Lineage Traversal Algorithm (Refined Architecture)

> **Specification for `agent.py`**  
> *Five-Stage Decoupled Engine: Acquisition → Normalization → Traversal → Rule Evaluation → Verdict Construction*

---

## 1. Five-Stage Decoupled Pipeline

```
┌────────────────────────┐
│  1. Graph Acquisition  │ ──► DataHub SDK Calls (get_aspect, execute_graphql)
└───────────┬────────────┘
            │ Raw Aspects & Entities
            ▼
┌────────────────────────┐
│ 2. Graph Normalization │ ──► Converts DataHub aspects to pure in-memory InternalGraph
└───────────┬────────────┘
            │ InternalGraph (nodes, edges, tags)
            ▼
┌────────────────────────┐
│   3. Graph Traversal   │ ──► Pure DFS/BFS in Python. ZERO SDK calls. Cycle-safe.
└───────────┬────────────┘
            │ TraversalPaths
            ▼
┌────────────────────────┐
│  4. Rule Evaluation    │ ──► Evaluates Leakage Policy & Incomplete Lineage Rules
└───────────┬────────────┘
            │ PolicyResult (leak_paths, incomplete_flag)
            ▼
┌────────────────────────┐
│5. Verdict Construction │ ──► Produces VerdictInternal data structure (no UI presentation strings)
└────────────────────────┘
```

---

## 2. In-Memory Graph Data Structures (`InternalGraph`)

```python
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional

@dataclass
class Node:
    urn: str
    type: str  # "mlModel" | "mlFeature" | "dataset" | "schemaField" | "unknown"
    name: str
    tags: Set[str] = field(default_factory=set)

@dataclass
class Edge:
    source_urn: str
    target_urn: str
    relationship_type: str  # "CONSUMES" | "DERIVED_FROM" | "LINEAGE"

@dataclass
class InternalGraph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    adjacency: Dict[str, List[str]] = field(default_factory=dict)  # source_urn -> list of target_urns

    def add_edge(self, source_urn: str, target_urn: str, rel_type: str = "LINEAGE"):
        self.edges.append(Edge(source_urn, target_urn, rel_type))
        self.adjacency.setdefault(source_urn, []).append(target_urn)
```

---

## 3. Five-Stage Algorithm Specification

### Stage 1: Graph Acquisition
Fetches raw DataHub aspects from DataHub server via `DataHubGraph`. All SDK calls are isolated in this stage.

### Stage 2: Graph Normalization
Constructs `InternalGraph` from raw DataHub aspects (`MLModelPropertiesClass`, `MLFeaturePropertiesClass`, `UpstreamLineageClass`, `GlobalTagsClass`).

### Stage 3: Graph Traversal
Traverses `InternalGraph` from `mlModel` root using Depth-First Search (DFS).
- **Cycle Prevention**: `visited` set per branch / global path tracking.
- **Max Depth**: Hard limit of 6 hops.
- **SDK Calls**: ZERO.

### Stage 4: Rule Evaluation
Evaluates paths in `InternalGraph`:
- **Leakage Rule**: Path contains node with tag `urn:li:tag:post_outcome` or `urn:li:tag:is_target`.
- **Incomplete Lineage Rule**: Traversal encounters node of type `unknown` or `mlFeature` with no outgoing edges.
- **Unknown Tags Rule**: Tags other than `post_outcome`/`is_target` do NOT trigger leakage.

### Stage 5: Verdict Construction
Constructs internal verdict dataclass:

```python
@dataclass
class EvidencePath:
    feature_urn: str
    tainted_urn: str
    tag_found: str
    path: List[str]

@dataclass
class VerdictInternal:
    model_urn: str
    verdict: str  # "blocked" | "approved"
    reason_code: str  # "TARGET_LEAKAGE" | "INCOMPLETE_LINEAGE" | "CLEAN"
    evidence_paths: List[EvidencePath]
    unresolved_nodes: List[str]
```

---

## 4. Required Unit Test Matrix (`test_agent.py`)

1. `test_leakage_detection_single_path()` — Red leak path detected on `post_outcome` tag.
2. `test_leakage_detection_multiple_paths()` — Multiple distinct leak paths captured simultaneously.
3. `test_clean_lineage_returns_approved()` — Complete untagged lineage passes.
4. `test_incomplete_lineage_returns_fail_closed()` — Lineage gap triggers fail-closed block.
5. `test_shared_upstream_nodes_deduplicated()` — Shared upstream tables traversed without duplication.
6. `test_unknown_tags_ignored()` — Non-leak tags (`pii`, `deprecated`) do not trigger target leakage block.
7. `test_cycle_prevention_terminates()` — Circular graph references terminate cleanly.
