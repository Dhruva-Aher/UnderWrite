# Underwrite — Write-Back Transaction & Idempotency Specification

> **Specification for Asynchronous Write-Back Processing (`datahub_client.py`)**  
> *Enforces Invariant 4: Write-Back is a pure side effect. Verdict generation NEVER depends on write-back.*

---

## 1. Architectural Flow (Event-Driven Side Effect)

```
POST /evaluate
   │
   ├─► 1. Execute agent.evaluate_model() ──► Generate VerdictInternal
   │
   ├─► 2. Return HTTP 200 Response Immediately to Client (UI updates instantly)
   │
   └─► 3. Fire-and-Forget Background Task:
          FastAPI BackgroundTask(process_verdict_writeback_event)
```

---

## 2. Failure Mode & Transaction Handling Matrix

| Scenario | Behavior | System Impact |
| :--- | :--- | :--- |
| **Partial failure** | Each operation is attempted independently up to three times. | The verdict has already been returned; a later evaluation request may retry an incomplete write-back. |
| **Existing tags or documentation** | Existing `GlobalTags` and `InstitutionalMemory` aspects are read and merged before emission. | Existing entries are preserved when the read succeeds. |
| **Graph / GMS unavailable** | The background worker logs the failure. | The API does not claim that the write succeeded. |
| **Duplicate incident** | Incident URNs are derived from dataset URN, model URN, and reason code. | Re-emitting the same governance incident targets the same entity. |

---

## 3. Idempotency & Deduplication Rules

1. **Deterministic keys**:
   - Tag: `urn:li:tag:model-at-risk` / `urn:li:tag:model-approved`
   - Incident: a stable hash of dataset URN, model URN, and reason code
   - Documentation: `institutionalMemory` aspect on model URN
2. **Session Deduplication**:
   - `datahub_client.py` maintains an in-memory `dedup_cache` keyed by
     `(model_urn, reason_code, request_id)`. Retries of the same evaluation are
     skipped; a later evaluation with a new `request_id` still writes.
   - Subsequent identical evaluations within the server lifetime skip redundant write-backs.
3. **Independent operations**:
   - Step 1: `write_tag()`
   - Step 2: `write_incident()` (emitted on dataset URN per GMS validation rules)
   - Step 3: `write_documentation()`
   - Failure in Step $N$ does not block Step $N+1$.
