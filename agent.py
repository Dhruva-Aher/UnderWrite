"""Underwrite — Core Detection Engine (agent.py)

Decoupled 5-Stage Architecture:
1. Graph Acquisition: Fetches raw aspects via MetadataClient.
2. Graph Normalization: Converts aspects into a pure in-memory InternalGraph.
3. Graph Traversal: Pure in-memory DFS graph walk. ZERO SDK calls during traversal.
4. Rule Evaluation: Evaluates Target Leakage and Incomplete Lineage policy rules via PolicyEvaluator.
5. Verdict Construction: Produces VerdictInternal data structure.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import datahub.metadata.schema_classes as sc
import yaml

from config import Settings
from config import settings as default_settings
from metadata.client import MetadataClient
from metadata.urns import (
    make_tag_urn,
)

logger = logging.getLogger("underwrite.agent")
MAX_LINEAGE_DEPTH = 6

TAG_POST_OUTCOME = make_tag_urn("post_outcome")
TAG_IS_TARGET = make_tag_urn("is_target")
LEAK_TAGS = {TAG_POST_OUTCOME, TAG_IS_TARGET, "post_outcome", "is_target"}


@dataclass
class Policy:
    policy_id: str
    name: str
    target_tags: set[str]
    description: str
    enabled: bool = True


TARGET_LEAKAGE_POLICY = Policy(
    policy_id="ML-LEAK-001",
    name="Target Leakage Prevention Policy",
    target_tags=LEAK_TAGS,
    description="Prevents models from training on features derived from post-outcome datasets.",
)


def load_policies_from_yaml(config_path: str = "policies.yaml") -> list[Policy]:
    """Load active policies from policies.yaml if present."""
    if not os.path.exists(config_path):
        return [TARGET_LEAKAGE_POLICY]
    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or not isinstance(data.get("policies", []), list):
            raise yaml.YAMLError("policy configuration must contain a policies list")

        loaded = []
        policy_ids: set[str] = set()
        for p in data.get("policies", []):
            if not isinstance(p, dict):
                raise yaml.YAMLError("each policy must be a mapping")
            if not p.get("enabled", True):
                continue
            policy_id = p.get("id")
            raw_tags = p.get("target_tags", [])
            if not isinstance(policy_id, str) or not policy_id.strip():
                raise yaml.YAMLError("each enabled policy must have a non-empty id")
            if policy_id in policy_ids:
                raise yaml.YAMLError(f"duplicate policy id: {policy_id}")
            if not isinstance(raw_tags, list) or not all(
                isinstance(tag, str) and tag for tag in raw_tags
            ):
                raise yaml.YAMLError("target_tags must be a list of non-empty strings")
            policy_ids.add(policy_id)
            tags = set(raw_tags)
            tags.update({make_tag_urn(tag) for tag in raw_tags})
            loaded.append(
                Policy(
                    policy_id=policy_id,
                    name=p.get("name", "Custom Policy"),
                    target_tags=tags,
                    description=p.get("description", ""),
                    enabled=p.get("enabled", True),
                )
            )
        logger.info("Loaded %d active policies from %s", len(loaded), config_path)
        return loaded if loaded else [TARGET_LEAKAGE_POLICY]
    except (yaml.YAMLError, OSError) as e:
        logger.warning(
            "Failed loading policies from %s (%s) — using default policy",
            config_path,
            e,
        )
        return [TARGET_LEAKAGE_POLICY]


# Stage 2 Data Structures
@dataclass
class Node:
    urn: str
    type: str  # "mlModel" | "mlFeature" | "dataset" | "schemaField" | "unknown"
    name: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Edge:
    source_urn: str
    target_urn: str
    relationship_type: str = "LINEAGE"


@dataclass
class InternalGraph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    adjacency: dict[str, list[str]] = field(default_factory=dict)

    def add_node(
        self, urn: str, type_: str, name: str, tags: set[str] | None = None
    ) -> None:
        """Add or update node entry in graph nodes dict."""
        if urn not in self.nodes:
            self.nodes[urn] = Node(urn=urn, type=type_, name=name, tags=tags or set())
        elif tags:
            self.nodes[urn].tags.update(tags)

    def add_edge(
        self, source_urn: str, target_urn: str, rel_type: str = "LINEAGE"
    ) -> None:
        """Add directed lineage edge to graph and update adjacency."""
        self.edges.append(Edge(source_urn, target_urn, rel_type))
        if target_urn not in self.adjacency.setdefault(source_urn, []):
            self.adjacency[source_urn].append(target_urn)


# Stage 5 Verdict Data Structures
@dataclass
class ExecutionEvent:
    stage: str
    step_num: int
    detail: str
    timestamp: str


@dataclass
class EvidencePath:
    feature_urn: str
    tainted_urn: str
    tag_found: str
    path: list[str]
    policy_id: str | None = None


@dataclass
class VerdictInternal:
    model_urn: str
    verdict: str  # "blocked" | "approved"
    reason_code: str  # "TARGET_LEAKAGE" | "INCOMPLETE_LINEAGE" | "CLEAN"
    evidence_paths: list[EvidencePath] = field(default_factory=list)
    unresolved_nodes: list[str] = field(default_factory=list)
    execution_events: list[ExecutionEvent] = field(default_factory=list)


# Stage 1: Graph Acquisition
class GraphAcquisition:
    """Fetches metadata aspects via MetadataClient abstraction."""

    def __init__(self, client: MetadataClient):
        self.client = client

    def acquire_model_aspects(self, model_urn: str) -> dict:
        """Acquire all relevant aspects for a model and its upstream hierarchy."""
        logger.info("Requesting aspects for model URN: %s", model_urn)
        model_props = self.client.get_aspect(model_urn, sc.MLModelPropertiesClass)
        if not model_props:
            logger.warning("Model properties not found for URN: %s", model_urn)
            return {"model_urn": model_urn, "model_props": None}

        features_data: dict[str, sc.MLFeaturePropertiesClass | None] = {}
        datasets_data: dict[str, dict[str, Any | None]] = {}

        for feat_urn in model_props.mlFeatures or []:
            feat_props = self.client.get_aspect(feat_urn, sc.MLFeaturePropertiesClass)
            features_data[feat_urn] = feat_props

            if feat_props and feat_props.sources:
                for ds_urn in feat_props.sources:
                    self._acquire_dataset_recursive(ds_urn, datasets_data, depth=0)

        # Fine-grained lineage identifies schema fields separately from their
        # datasets. Read tags on those field entities so a column-level policy
        # can evaluate the actual provenance node, not a dataset-wide proxy.
        for ds_data in datasets_data.values():
            lineage = ds_data.get("lineage")
            field_tags: dict[str, Any] = {}
            for fg in getattr(lineage, "fineGrainedLineages", []) or []:
                for field_urn in [*(fg.upstreams or []), *(fg.downstreams or [])]:
                    field_tags[field_urn] = self.client.get_aspect(
                        field_urn, sc.GlobalTagsClass
                    )
            ds_data["field_tags"] = field_tags

        logger.info(
            "Acquired %d features, %d datasets for model %s",
            len(features_data),
            len(datasets_data),
            model_urn,
        )
        return {
            "model_urn": model_urn,
            "model_props": model_props,
            "features_data": features_data,
            "datasets_data": datasets_data,
        }

    def _acquire_dataset_recursive(
        self,
        ds_urn: str,
        datasets_data: dict[str, dict[str, Any | None]],
        depth: int,
    ) -> None:
        """Recursively fetch properties, lineage, and tag aspects for upstream datasets."""
        if ds_urn in datasets_data or depth > MAX_LINEAGE_DEPTH:
            return

        ds_props = self.client.get_aspect(ds_urn, sc.DatasetPropertiesClass)
        lineage_props = self.client.get_aspect(ds_urn, sc.UpstreamLineageClass)
        tags_props = self.client.get_aspect(ds_urn, sc.GlobalTagsClass)

        datasets_data[ds_urn] = {
            "props": ds_props,
            "lineage": lineage_props,
            "tags": tags_props,
            "truncated": bool(
                depth >= MAX_LINEAGE_DEPTH
                and lineage_props
                and lineage_props.upstreams
            ),
        }

        if lineage_props and lineage_props.upstreams and depth < MAX_LINEAGE_DEPTH:
            for upstream in lineage_props.upstreams:
                if upstream and getattr(upstream, "dataset", None):
                    self._acquire_dataset_recursive(
                        upstream.dataset, datasets_data, depth + 1
                    )


# Stage 2: Graph Normalization
def normalize_to_internal_graph(acquired_data: dict) -> InternalGraph:
    """Converts raw aspect dictionaries into a pure in-memory InternalGraph."""
    ig = InternalGraph()
    model_urn = acquired_data["model_urn"]
    model_props = acquired_data.get("model_props")

    if not model_props:
        ig.add_node(model_urn, "unknown", model_urn)
        return ig

    ig.add_node(model_urn, "mlModel", model_props.name or model_urn)

    features_data = acquired_data.get("features_data", {})
    datasets_data = acquired_data.get("datasets_data", {})

    for feat_urn, feat_props in features_data.items():
        if not feat_props:
            ig.add_node(feat_urn, "unknown", feat_urn)
            ig.add_edge(model_urn, feat_urn, "CONSUMES")
            continue

        ig.add_node(feat_urn, "mlFeature", feat_urn)
        ig.add_edge(model_urn, feat_urn, "CONSUMES")

        sources = feat_props.sources or []
        if not sources:
            unknown_src = f"unknown:{feat_urn}"
            ig.add_node(unknown_src, "unknown", "Unresolved Source")
            ig.add_edge(feat_urn, unknown_src, "DERIVED_FROM")

        for ds_urn in sources:
            ig.add_edge(feat_urn, ds_urn, "DERIVED_FROM")

    for ds_urn, ds_data in datasets_data.items():
        ds_props = ds_data.get("props")
        if not ds_props:
            ig.add_node(ds_urn, "unknown", ds_urn)
            continue

        ds_name = ds_props.name
        tags_aspect = ds_data.get("tags")

        tags_set = set()
        if tags_aspect and tags_aspect.tags:
            tags_set = {t.tag for t in tags_aspect.tags}

        ig.add_node(ds_urn, "dataset", ds_name, tags_set)

        lineage_aspect = ds_data.get("lineage")
        if lineage_aspect:
            if lineage_aspect.upstreams:
                for upstream in lineage_aspect.upstreams:
                    ig.add_edge(ds_urn, upstream.dataset, "LINEAGE")

            if lineage_aspect.fineGrainedLineages:
                for fg in lineage_aspect.fineGrainedLineages:
                    for up_field in fg.upstreams or []:
                        up_tags = ds_data.get("field_tags", {}).get(up_field)
                        up_tag_set = {
                            t.tag for t in getattr(up_tags, "tags", []) or []
                        }
                        ig.add_node(up_field, "schemaField", up_field, up_tag_set)
                        for down_field in fg.downstreams or []:
                            down_tags = ds_data.get("field_tags", {}).get(down_field)
                            down_tag_set = {
                                t.tag for t in getattr(down_tags, "tags", []) or []
                            }
                            ig.add_node(
                                down_field, "schemaField", down_field, down_tag_set
                            )
                            ig.add_edge(ds_urn, down_field, "CONTAINS_FIELD")
                            ig.add_edge(down_field, up_field, "LINEAGE")

        if ds_data.get("truncated"):
            unknown_src = f"unknown:depth:{ds_urn}"
            ig.add_node(unknown_src, "unknown", "Lineage depth limit reached")
            ig.add_edge(ds_urn, unknown_src, "TRUNCATED")

    logger.info(
        "Converted %d nodes and %d edges into InternalGraph",
        len(ig.nodes),
        len(ig.edges),
    )
    return ig


# Stage 3 & 4: Traversal & Policy Engine
class PolicyEvaluator:
    """Evaluates governance policies over in-memory InternalGraph."""

    def __init__(self, policy: Policy = TARGET_LEAKAGE_POLICY):
        self.policy = policy

    def evaluate(self, graph: InternalGraph, root_urn: str) -> VerdictInternal:
        logger.info("Starting DFS walk from root model: %s", root_urn)
        evidence_paths: list[EvidencePath] = []
        unresolved_nodes: list[str] = []

        if root_urn not in graph.nodes or graph.nodes[root_urn].type == "unknown":
            logger.warning("Model root URN unresolved: %s", root_urn)
            return VerdictInternal(
                model_urn=root_urn,
                verdict="blocked",
                reason_code="INCOMPLETE_LINEAGE",
                unresolved_nodes=[root_urn],
            )

        feature_urns = graph.adjacency.get(root_urn, [])

        for feat_urn in feature_urns:
            visited_in_path: set[str] = set()
            self._dfs_evaluate(
                graph=graph,
                curr_urn=feat_urn,
                feat_urn=feat_urn,
                path=[root_urn, feat_urn],
                visited=visited_in_path,
                evidence_paths=evidence_paths,
                unresolved_nodes=unresolved_nodes,
                depth=0,
            )

        if evidence_paths:
            logger.info(
                "Policy %s triggered on %s",
                self.policy.policy_id,
                evidence_paths[0].tainted_urn,
            )
            return VerdictInternal(
                model_urn=root_urn,
                verdict="blocked",
                reason_code="TARGET_LEAKAGE",
                evidence_paths=evidence_paths,
                unresolved_nodes=unresolved_nodes,
            )
        elif unresolved_nodes:
            logger.warning(
                "Incomplete lineage detected for nodes: %s", unresolved_nodes
            )
            return VerdictInternal(
                model_urn=root_urn,
                verdict="blocked",
                reason_code="INCOMPLETE_LINEAGE",
                evidence_paths=[],
                unresolved_nodes=unresolved_nodes,
            )
        else:
            logger.info("Policy check clean — zero violations found")
            return VerdictInternal(
                model_urn=root_urn,
                verdict="approved",
                reason_code="CLEAN",
                evidence_paths=[],
                unresolved_nodes=[],
            )

    def _dfs_evaluate(
        self,
        graph: InternalGraph,
        curr_urn: str,
        feat_urn: str,
        path: list[str],
        visited: set[str],
        evidence_paths: list[EvidencePath],
        unresolved_nodes: list[str],
        depth: int,
    ) -> None:
        if curr_urn in visited:
            return

        if depth > MAX_LINEAGE_DEPTH:
            if curr_urn not in unresolved_nodes:
                unresolved_nodes.append(curr_urn)
            return

        visited.add(curr_urn)
        node = graph.nodes.get(curr_urn)

        if not node or node.type == "unknown":
            if curr_urn not in unresolved_nodes:
                unresolved_nodes.append(curr_urn)
            return

        intersecting_tags = node.tags.intersection(self.policy.target_tags)
        if intersecting_tags:
            tag_found = min(intersecting_tags)
            evidence_paths.append(
                EvidencePath(
                    feature_urn=feat_urn,
                    tainted_urn=curr_urn,
                    tag_found=tag_found,
                    path=list(path),
                    policy_id=self.policy.policy_id,
                )
            )

        neighbors = graph.adjacency.get(curr_urn, [])
        for next_urn in neighbors:
            self._dfs_evaluate(
                graph=graph,
                curr_urn=next_urn,
                feat_urn=feat_urn,
                path=path + [next_urn],
                visited=visited,
                evidence_paths=evidence_paths,
                unresolved_nodes=unresolved_nodes,
                depth=depth + 1,
            )


class Agent:
    """Governance Agent evaluating policies via explicit Dependency Injection."""

    def __init__(
        self,
        client: MetadataClient,
        settings: Settings = default_settings,
        logger: logging.Logger | None = None,
    ):
        self.client = client
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)
        self.policies = load_policies_from_yaml(self.settings.policy_path)
        self.last_graph: InternalGraph | None = None

    def evaluate_model(self, model_urn: str) -> VerdictInternal:
        """Run the 5-stage evaluation pipeline."""
        acq = GraphAcquisition(self.client)
        acquired_data = acq.acquire_model_aspects(model_urn)
        internal_graph = normalize_to_internal_graph(acquired_data)
        self.last_graph = internal_graph
        events = [
            ExecutionEvent(
                "Acquisition", 1,
                f"Read {len(acquired_data.get('features_data', {}))} features and {len(acquired_data.get('datasets_data', {}))} datasets from DataHub.",
                datetime.now(timezone.utc).isoformat(),
            ),
            ExecutionEvent(
                "Normalization", 2,
                f"Normalized {len(internal_graph.nodes)} nodes and {len(internal_graph.edges)} lineage edges.",
                datetime.now(timezone.utc).isoformat(),
            ),
        ]
        # Evaluate every enabled policy in configuration order. The first
        # blocking result is deterministic and preserves its policy evidence.
        for policy in self.policies or [TARGET_LEAKAGE_POLICY]:
            verdict = PolicyEvaluator(policy=policy).evaluate(internal_graph, model_urn)
            if verdict.verdict == "blocked":
                if (
                    verdict.reason_code == "TARGET_LEAKAGE"
                    and policy.policy_id != TARGET_LEAKAGE_POLICY.policy_id
                ):
                    verdict.reason_code = f"POLICY_VIOLATION:{policy.policy_id}"
                verdict.execution_events = events + [
                    ExecutionEvent(
                        "Decision", 3,
                        f"Blocked by {verdict.reason_code}.",
                        datetime.now(timezone.utc).isoformat(),
                    )
                ]
                return verdict
        return VerdictInternal(
            model_urn=model_urn,
            verdict="approved",
            reason_code="CLEAN",
            execution_events=events + [
                ExecutionEvent(
                    "Decision", 3,
                    "Approved after all configured policies completed without a match.",
                    datetime.now(timezone.utc).isoformat(),
                )
            ],
        )


def traverse_and_evaluate(graph: InternalGraph, root_urn: str) -> VerdictInternal:
    """Helper wrapper for backwards compatibility with unit tests."""
    evaluator = PolicyEvaluator()
    return evaluator.evaluate(graph, root_urn)


def evaluate_model(model_urn: str, datahub_graph) -> VerdictInternal:
    """Backwards-compatible wrapper accepting raw graph or client."""
    if hasattr(datahub_graph, "get_aspect"):
        client = datahub_graph
    else:
        from metadata.client import DataHubClient

        client = DataHubClient(default_settings.gms_url)
    agent = Agent(client=client)
    return agent.evaluate_model(model_urn)
