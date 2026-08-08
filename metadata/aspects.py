"""Aspect construction utilities and schema helpers for DataHub metadata."""

import time
from hashlib import sha256

import datahub.metadata.schema_classes as sc
from datahub.emitter.mcp import MetadataChangeProposalWrapper


def build_tag_mcp(
    target_urn: str, tag_name: str, existing_tags: list[sc.TagAssociationClass] | None = None
) -> MetadataChangeProposalWrapper:
    """Build a MetadataChangeProposal for attaching a tag to an entity URN."""
    tag_association = sc.TagAssociationClass(tag=f"urn:li:tag:{tag_name}")
    tags = list(existing_tags or [])
    if not any(tag.tag == tag_association.tag for tag in tags):
        tags.append(tag_association)
    tags_aspect = sc.GlobalTagsClass(tags=tags)
    return MetadataChangeProposalWrapper(
        entityUrn=target_urn,
        aspect=tags_aspect,
    )


def build_incident_mcp(
    dataset_urn: str,
    model_urn: str,
    incident_type: str,
    description: str,
) -> MetadataChangeProposalWrapper:
    """Build a MetadataChangeProposal for raising an Incident aspect on a dataset.

    DataHub's IncidentInfo.type is a closed enum. Policy reason codes are stored
    in customType with type=CUSTOM.
    """
    now_ms = int(time.time() * 1000)
    stamp = sc.AuditStampClass(
        time=now_ms,
        actor="urn:li:corpuser:underwrite-agent",
    )
    incident_aspect = sc.IncidentInfoClass(
        type=sc.IncidentTypeClass.CUSTOM,
        customType=str(incident_type),
        entities=[dataset_urn],
        title=f"Governance Audit Warning: {incident_type}",
        description=f"Raised for downstream model {model_urn}: {description}",
        status=sc.IncidentStatusClass(
            state=sc.IncidentStateClass.ACTIVE,
            lastUpdated=stamp,
        ),
        created=stamp,
    )
    incident_key = sha256(
        f"{dataset_urn}|{model_urn}|{incident_type}".encode()
    ).hexdigest()[:20]
    incident_urn = f"urn:li:incident:underwrite-{incident_key}"
    return MetadataChangeProposalWrapper(
        entityUrn=incident_urn,
        aspect=incident_aspect,
    )


def build_documentation_mcp(
    target_urn: str,
    text: str,
    existing_elements: list[sc.InstitutionalMemoryMetadataClass] | None = None,
) -> MetadataChangeProposalWrapper:
    """Build a MetadataChangeProposal for writing Institutional Memory documentation."""
    doc_element = sc.InstitutionalMemoryMetadataClass(
        url=f"https://underwrite.local/audits/{int(time.time())}",
        description=f"[Underwrite Verdict] {text}",
        createStamp=sc.AuditStampClass(
            time=int(time.time() * 1000),
            actor="urn:li:corpuser:underwrite-agent",
        ),
    )
    elements = list(existing_elements or [])
    if not any(element.description == doc_element.description for element in elements):
        elements.append(doc_element)
    memory_aspect = sc.InstitutionalMemoryClass(elements=elements)
    return MetadataChangeProposalWrapper(
        entityUrn=target_urn,
        aspect=memory_aspect,
    )
