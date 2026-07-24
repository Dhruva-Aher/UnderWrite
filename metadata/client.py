"""Metadata client interface and implementations (DataHub SDK client & Mock in-memory client)."""

import logging
from typing import Any, Protocol

import requests
import datahub.metadata.schema_classes as sc

from exceptions import (
    AuthenticationError,
    NetworkError,
    UnderwriteError,
)
from metadata.aspects import (
    build_documentation_mcp,
    build_incident_mcp,
    build_tag_mcp,
)

logger = logging.getLogger(__name__)


class MetadataClient(Protocol):
    """Abstract domain interface for metadata graph interactions."""

    def get_aspect(self, entity_urn: str, aspect_type: Any) -> Any | None:
        """Fetch a specific aspect for an entity URN."""
        ...

    def is_healthy(self) -> bool:
        """Return whether the backing metadata service is reachable."""
        ...

    def write_verdict_tag(self, target_urn: str, tag_name: str) -> bool:
        """Attach a governance verdict tag to an entity URN."""
        ...

    def write_incident(
        self,
        dataset_urn: str,
        model_urn: str,
        incident_type: str,
        description: str,
    ) -> bool:
        """Raise a governance incident aspect on a dataset/model URN."""
        ...

    def write_documentation(self, target_urn: str, text: str) -> bool:
        """Write governance audit notes to entity institutional memory."""
        ...


class DataHubClient(MetadataClient):
    """Concrete DataHub SDK client using REST emitter and DataHubGraph."""

    def __init__(self, gms_url: str):
        self.gms_url = gms_url
        self._emitter = None
        self._graph = None

    def _get_emitter(self):
        if self._emitter is None:
            from datahub.emitter.rest_emitter import DatahubRestEmitter

            self._emitter = DatahubRestEmitter(self.gms_url)
        return self._emitter

    def _get_graph(self):
        if self._graph is None:
            from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph

            self._graph = DataHubGraph(DatahubClientConfig(server=self.gms_url))
        return self._graph

    def is_healthy(self) -> bool:
        """Check GMS without issuing an invalid aspect request."""
        try:
            response = requests.get(f"{self.gms_url.rstrip('/')}/healthcheck", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.warning("DataHub GMS health check failed at %s: %s", self.gms_url, e)
            return False

    def get_aspect(self, entity_urn: str, aspect_type: Any) -> Any | None:
        """Fetch a specific aspect from DataHub graph with domain error translation."""
        try:
            graph = self._get_graph()
            return graph.get_aspect(entity_urn, aspect_type)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 403:
                logger.error(
                    "Authentication failed accessing DataHub GMS at %s (403 Forbidden)",
                    self.gms_url,
                )
                raise AuthenticationError(f"GMS Forbidden: {e}") from e
            logger.warning("HTTP error querying aspect for %s: %s", entity_urn, e)
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.warning(
                "DataHub GMS connection unreachable at %s: %s", self.gms_url, e
            )
            raise NetworkError(f"GMS Unreachable at {self.gms_url}") from e
        except (
            requests.exceptions.RequestException,
            UnderwriteError,
            RuntimeError,
            ValueError,
            AssertionError,
        ) as e:
            logger.warning("Failed to fetch aspect for %s: %s", entity_urn, e)
            return None

    def write_verdict_tag(self, target_urn: str, tag_name: str) -> bool:
        """Emit a tag MCP to DataHub GMS."""
        try:
            current = self.get_aspect(target_urn, sc.GlobalTagsClass)
            mcp = build_tag_mcp(target_urn, tag_name, getattr(current, "tags", None))
            emitter = self._get_emitter()
            emitter.emit(mcp)
            logger.info("Successfully emitted tag %s for URN %s", tag_name, target_urn)
            return True
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 403:
                logger.warning(
                    "Tag write forbidden (403) for %s — non-blocking", target_urn
                )
                return False
            logger.warning("Tag write HTTP error for %s: %s", target_urn, e)
            return False
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.warning(
                "Tag write network error for %s: %s — non-blocking", target_urn, e
            )
            return False
        except (
            requests.exceptions.RequestException,
            UnderwriteError,
            RuntimeError,
            ValueError,
            AssertionError,
        ) as e:
            logger.warning("Tag write failed for %s: %s — non-blocking", target_urn, e)
            return False

    def write_incident(
        self,
        dataset_urn: str,
        model_urn: str,
        incident_type: str,
        description: str,
    ) -> bool:
        """Emit an incident MCP to DataHub GMS."""
        try:
            mcp = build_incident_mcp(dataset_urn, model_urn, incident_type, description)
            emitter = self._get_emitter()
            emitter.emit(mcp)
            logger.info(
                "Successfully emitted incident %s for model URN %s",
                incident_type,
                model_urn,
            )
            return True
        except (
            requests.exceptions.RequestException,
            UnderwriteError,
            RuntimeError,
            ValueError,
            AssertionError,
        ) as e:
            logger.warning(
                "Incident write failed for %s: %s — non-blocking", model_urn, e
            )
            return False

    def write_documentation(self, target_urn: str, text: str) -> bool:
        """Emit documentation memory MCP to DataHub GMS."""
        try:
            current = self.get_aspect(target_urn, sc.InstitutionalMemoryClass)
            mcp = build_documentation_mcp(
                target_urn, text, getattr(current, "elements", None)
            )
            emitter = self._get_emitter()
            emitter.emit(mcp)
            logger.info("Successfully emitted documentation for URN %s", target_urn)
            return True
        except (
            requests.exceptions.RequestException,
            UnderwriteError,
            RuntimeError,
            ValueError,
        ) as e:
            logger.warning(
                "Documentation write failed for %s: %s — non-blocking", target_urn, e
            )
            return False


class MockMetadataClient(MetadataClient):
    """In-memory mock metadata client for zero-network unit testing."""

    def __init__(self, seeded_aspects: dict[str, dict[Any, Any]] | None = None):
        self.aspects: dict[str, dict[Any, Any]] = seeded_aspects or {}
        self.emitted_tags: list[dict[str, str]] = []
        self.emitted_incidents: list[dict[str, str]] = []
        self.emitted_docs: list[dict[str, str]] = []

    def get_aspect(self, entity_urn: str, aspect_type: Any) -> Any | None:
        return self.aspects.get(entity_urn, {}).get(aspect_type)

    def is_healthy(self) -> bool:
        return True

    def write_verdict_tag(self, target_urn: str, tag_name: str) -> bool:
        self.emitted_tags.append({"target_urn": target_urn, "tag_name": tag_name})
        return True

    def write_incident(
        self,
        dataset_urn: str,
        model_urn: str,
        incident_type: str,
        description: str,
    ) -> bool:
        self.emitted_incidents.append(
            {
                "dataset_urn": dataset_urn,
                "model_urn": model_urn,
                "incident_type": incident_type,
                "description": description,
            }
        )
        return True

    def write_documentation(self, target_urn: str, text: str) -> bool:
        self.emitted_docs.append({"target_urn": target_urn, "text": text})
        return True
