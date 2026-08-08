"""Underwrite — DataHub Write-Back Engine (datahub_client.py)

Enforces Invariant 4: Write-back is a pure side effect.
Verdict generation and UI rendering NEVER depend on write-back success.
"""

import logging
import time

from config import settings, Settings
from metadata.client import DataHubClient, MetadataClient
from metadata.urns import (
    make_tag_urn,
    dataset_urn_from_maybe_schema_field,
)
from pydantic import BaseModel

logger = logging.getLogger("underwrite.writeback")

# In-memory deduplication cache: (model_urn, reason_code)
_DEDUP_CACHE: set[tuple[str, str]] = set()
MAX_WRITE_ATTEMPTS = 3

TAG_MODEL_AT_RISK_URN = make_tag_urn("model-at-risk")
TAG_MODEL_APPROVED_URN = make_tag_urn("model-approved")


class WritebackResult(BaseModel):
    status: str
    message: str


def create_datahub_client(config: Settings) -> DataHubClient:
    """Central factory for DataHubClient creation with settings-derived credentials."""
    return DataHubClient(
        gms_url=config.gms_url,
        token=config.datahub_token,
    )


class DataHubWriteBackClient:
    """Handles write-back side effects to DataHub GMS asynchronously."""

    def __init__(
        self, gms_url: str | None = None, client: MetadataClient | None = None
    ):
        self.gms_url = gms_url or settings.gms_url
        self.client = client or create_datahub_client(settings)

    def write_tag(self, model_urn: str, tag_urn: str) -> bool:
        """Apply global tag to model entity idempotently."""
        # Convert tag URN to simple tag name if necessary
        tag_name = tag_urn.split(":")[-1] if ":" in tag_urn else tag_urn
        return self.client.write_verdict_tag(model_urn, tag_name)

    def write_incident(
        self, dataset_urn: str, model_urn: str, reason_code: str, description: str
    ) -> bool:
        """Create operational incident on upstream dataset entity."""
        return self.client.write_incident(
            dataset_urn, model_urn, reason_code, description
        )

    def write_documentation(self, model_urn: str, summary: str) -> bool:
        """Append audit verdict documentation entry to model entity."""
        return self.client.write_documentation(model_urn, summary)


def normalize_writeback_payload(verdict_data: dict) -> dict:
    """Accept flat demo payloads or nested /evaluate API responses."""
    request = verdict_data.get("request") or {}
    evaluation = verdict_data.get("evaluation") or {}
    return {
        "model_urn": verdict_data.get("model_urn") or request.get("model_urn"),
        "reason_code": verdict_data.get("reason_code") or evaluation.get("reason_code"),
        "verdict": verdict_data.get("verdict") or evaluation.get("verdict"),
        "evidence_paths": verdict_data.get("evidence_paths", []),
        "headline": verdict_data.get("headline") or evaluation.get("headline"),
    }


def process_verdict_writeback_event(
    verdict_data: dict,
    gms_url: str | None = None,
    client: MetadataClient | None = None,
) -> WritebackResult:
    """Event-driven background worker. Fired asynchronously after evaluate."""
    verdict_data = normalize_writeback_payload(verdict_data)
    model_urn = verdict_data.get("model_urn")
    reason_code = verdict_data.get("reason_code")
    verdict = verdict_data.get("verdict")
    if hasattr(verdict, "value"):
        verdict = verdict.value

    if not model_urn or not reason_code:
        return WritebackResult(status="SKIPPED", message="Missing required verdict data")

    cache_key = (model_urn, reason_code)
    if cache_key in _DEDUP_CACHE:
        logger.info(
            "Skipping duplicate write-back event for model %s (rule %s)",
            model_urn,
            reason_code,
        )
        return WritebackResult(status="SKIPPED", message="Duplicate write-back event")
    wb_client = DataHubWriteBackClient(gms_url=gms_url, client=client)

    def attempt(operation) -> bool:
        for attempt_num in range(MAX_WRITE_ATTEMPTS):
            if operation():
                return True
            if attempt_num < MAX_WRITE_ATTEMPTS - 1:
                time.sleep(0.2 * (attempt_num + 1))
        return False

    try:
        if verdict == "blocked":
            outcomes = [
                attempt(lambda: wb_client.write_tag(model_urn, TAG_MODEL_AT_RISK_URN))
            ]

            evidence_paths = verdict_data.get("evidence_paths", [])
            target_ds = None
            if evidence_paths:
                ep0 = evidence_paths[0]
                if isinstance(ep0, dict):
                    target_ds = ep0.get("tainted_urn")
                elif hasattr(ep0, "tainted_urn"):
                    target_ds = ep0.tainted_urn

            if isinstance(target_ds, str) and target_ds.startswith("urn:li:schemaField:("):
                target_ds = dataset_urn_from_maybe_schema_field(target_ds)

            desc = verdict_data.get(
                "headline", "Underwrite evaluation blocked model deployment."
            )
            
            if target_ds:
                outcomes.append(
                    attempt(
                        lambda: wb_client.write_incident(
                            target_ds, model_urn, reason_code, desc
                        )
                    )
                )
            else:
                logger.info("Incident SKIPPED: no evidence entity available")
            outcomes.append(
                attempt(
                    lambda: wb_client.write_documentation(
                        model_urn, f"BLOCKED ({reason_code})"
                    )
                )
            )

        elif verdict == "approved" or (hasattr(verdict, "value") and verdict.value == "approved"):
            outcomes = [
                attempt(lambda: wb_client.write_tag(model_urn, TAG_MODEL_APPROVED_URN)),
                attempt(lambda: wb_client.write_documentation(model_urn, "APPROVED (CLEAN)")),
            ]
        else:
            return WritebackResult(status="SKIPPED", message="Unknown verdict")

        if all(outcomes):
            _DEDUP_CACHE.add(cache_key)
            is_mock = client is not None and type(client).__name__ == "MockMetadataClient"
            msg = (
                "In-memory mock write-back complete (not GMS)"
                if is_mock
                else "DataHub GMS write-back complete"
            )
            return WritebackResult(status="SUCCESS", message=msg)
        else:
            logger.warning("DataHub write-back incomplete for %s; event remains retryable", model_urn)
            return WritebackResult(status="INCOMPLETE", message="Write-back incomplete")
    except Exception as e:
        logger.warning("DataHub background write-back skipped (GMS offline: %s)", e)
        return WritebackResult(status="ERROR", message=f"Write-back exception: {e}")
