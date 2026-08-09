

import { parseUrn } from "@/lib/urn";
import { useState, createContext, useContext } from "react";
import { Verdict } from "@/lib/underwrite-data";
import GraphVisualizer from "./GraphVisualizer";

/* ---------- canonical-URN disclosure ---------- */

const UrnModeContext = createContext(false);

/**
 * Friendly name first, canonical URN on demand.
 * The URN is never removed — it is one click (or one global toggle) away.
 */
function UrnRef({
  value,
  showEntity = true,
  className = "",
}: {
  value: string;
  showEntity?: boolean;
  className?: string;
}) {
  const globalOpen = useContext(UrnModeContext);
  const [open, setOpen] = useState(false);
  const parsed = parseUrn(value);
  const expanded = open || globalOpen;

  if (parsed.raw === "—" || !parsed.raw) {
    return <span className="font-mono text-[11px] text-muted-foreground">—</span>;
  }

  return (
    <span className={`inline-flex min-w-0 flex-col gap-0.5 ${className}`}>
      <span className="flex min-w-0 flex-wrap items-center gap-1.5">
        {showEntity ? (
          <span className="border border-border px-1 py-px font-mono text-[10px] text-muted-foreground">
            {parsed.entity}
          </span>
        ) : null}
        <span className="min-w-0 font-mono text-[12px] break-all text-foreground" title={parsed.label}>
          {parsed.label}
        </span>
        {parsed.qualifier ? (
          <span className="font-mono text-[10px] text-muted-foreground">{parsed.qualifier}</span>
        ) : null}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setOpen((v) => !v);
          }}
          aria-expanded={expanded}
          aria-label={expanded ? "Hide canonical URN" : "Show canonical URN"}
          className="border border-border px-1 py-px font-mono text-[9px] tracking-[0.08em] text-muted-foreground uppercase transition-colors hover:border-ring hover:text-metadata"
        >
          urn
        </button>
      </span>
      {expanded ? (
        <code className="block font-mono text-[10px] leading-4 break-all text-metadata">
          {parsed.raw}
        </code>
      ) : null}
    </span>
  );
}

/* ---------- primitives ---------- */

function VerdictChip({ verdict, size = "sm" }: { verdict: Verdict; size?: "sm" | "md" }) {
  const map: Record<Verdict, string> = {
    APPROVED: "border-approved/50 text-approved bg-approved-dim/40",
    BLOCKED: "border-blocked/50 text-blocked bg-blocked-dim/40",
    WARN: "border-warning/50 text-warning bg-warning-dim/40",
  };
  return (
    <span
      className={`inline-flex items-center border font-mono tracking-[0.08em] uppercase ${map[verdict]} ${
        size === "md" ? "px-2 py-1 text-[12px] font-semibold" : "px-1.5 py-0.5 text-[10px]"
      }`}
    >
      {verdict}
    </span>
  );
}

function StatusText({ value }: { value: string }) {
  const tone =
    value === "VERIFIED"
      ? "text-approved"
      : value === "REQUESTED"
        ? "text-blue-400"
        : value === "PENDING_REVIEW"
          ? "text-warning"
          : "text-muted-foreground";
  return <span className={`font-mono text-[11px] ${tone}`}>{value}</span>;
}

function Arrow() {
  return (
    <span aria-hidden className="font-mono text-[12px] text-border-strong">
      →
    </span>
  );
}

function Section({
  index,
  title,
  meta,
  children,
}: {
  index: string;
  title: string;
  meta?: string;
  children: React.ReactNode;
}) {
  return (
    <section aria-labelledby={`sec-${index}`} className="border-b border-border">
      <header className="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-border bg-surface px-4 py-2">
        <span className="font-mono text-[11px] text-muted-foreground">{index}</span>
        <h2 id={`sec-${index}`} className="text-[13px] font-semibold tracking-tight">
          {title}
        </h2>
        {meta ? <span className="label-xs ml-auto">{meta}</span> : null}
      </header>
      {children}
    </section>
  );
}

/* ---------- 01 request ---------- */

function RequestBar({
  onEvaluate,
  state,
  request,
  evalSource,
}: {
  onEvaluate: () => void;
  state: "idle" | "running" | "done" | "error";
  request: {
    model_urn: string;
    environment: string;
    action: string;
    requested_by: string;
    request_id: string;
  };
  evalSource: string;
}) {
  const sourceLabel =
    evalSource === "live_datahub"
      ? "DataHub: Live GMS"
      : evalSource === "not_evaluated"
        ? "Not evaluated"
        : evalSource === "unavailable"
          ? "DataHub: Unavailable (fail-closed)"
          : `Source: ${evalSource}`;
  const sourceTone =
    evalSource === "live_datahub"
      ? "border-approved/60 text-approved bg-approved-dim/40"
      : evalSource === "not_evaluated"
        ? "border-border text-muted-foreground"
        : "border-warning/60 bg-warning-dim/40 text-warning";

  return (
    <div className="grid grid-cols-1 gap-px bg-border lg:grid-cols-[1fr_auto]">
      <dl className="grid grid-cols-1 gap-px bg-border sm:grid-cols-2 xl:grid-cols-4">
        <div className="bg-surface px-4 py-2.5">
          <dt className="label-xs">Subject</dt>
          <dd className="mt-1">
            <UrnRef value={request.model_urn} showEntity={false} />
          </dd>
        </div>
        <div className="bg-surface px-4 py-2.5">
          <dt className="label-xs">Target Environment</dt>
          <dd className="mt-1 font-mono text-[12px]">{request.environment}</dd>
        </div>
        <div className="bg-surface px-4 py-2.5">
          <dt className="label-xs">Requested Operation</dt>
          <dd className="mt-1 font-mono text-[12px]">{request.action}</dd>
        </div>
        <div className="bg-surface px-4 py-2.5">
          <dt className="label-xs">Principal</dt>
          <dd className="mt-1">
            <UrnRef value={request.requested_by} showEntity={false} />
          </dd>
        </div>
      </dl>
      <div className="flex items-center gap-3 bg-surface px-4 py-3">
        <button
          type="button"
          onClick={onEvaluate}
          disabled={state === "running"}
          className="border border-border-strong bg-surface-raised px-3 py-1.5 font-mono text-[11px] tracking-[0.08em] uppercase transition-colors hover:border-ring hover:bg-accent disabled:opacity-60"
        >
          {state === "running" ? "Evaluating…" : "Evaluate Trust"}
        </button>
        <span className="label-xs whitespace-nowrap">{request.request_id}</span>
        <span className={`ml-auto inline-flex items-center px-2 py-1 text-[11px] font-mono border uppercase tracking-[0.08em] ${sourceTone}`}>
          {sourceLabel}
        </span>
      </div>
    </div>
  );
}

function HonestBanner() {
  return (
    <div className="border-b border-border bg-surface px-4 py-2 font-mono text-[11px] text-muted-foreground">
      Authoritative path: <span className="text-foreground">POST /evaluate</span> +{" "}
      <span className="text-foreground">scripts/deployment_gate.py</span>. This console displays that
      response; it does not invent a live DataHub connection.
    </div>
  );
}

/* ---------- 02 decision ---------- */


function DecisionBanner({
  evaluated,
  EVAL,
  WRITEBACK,
  evidenceCount,
}: {
  evaluated: boolean;
  EVAL: any;
  WRITEBACK: any[];
  evidenceCount: number;
}) {
  const denies = EVAL.denials ?? 0;
  const writebackAspects = Array.from(new Set((WRITEBACK || []).map((w: any) => w.aspect).filter(Boolean)));
  const verdict = String(EVAL.verdict || "").toUpperCase();
  const isBlocked = verdict === "BLOCKED";
  const verdictColor = !evaluated
    ? "text-muted-foreground"
    : isBlocked
      ? "text-blocked"
      : "text-approved";
  const borderColor = !evaluated
    ? "border-l-border-strong bg-surface"
    : isBlocked
      ? "border-l-blocked bg-blocked-dim/25"
      : "border-l-approved bg-approved-dim/25";

  return (
    <div role="status" aria-live="polite" className={`border-l-2 px-4 py-8 ${borderColor}`}>
      <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
        <span className="label-xs">
          {EVAL.action || "DEPLOY"} · {EVAL.environment || "PROD"}
        </span>
        <span className={`mt-2 font-mono text-[80px] leading-none font-bold tracking-tight ${verdictColor}`}>
          {evaluated ? verdict || "UNKNOWN" : "NOT EVALUATED"}
        </span>
        <p className="mt-3 text-[17px] font-medium text-foreground">
          {evaluated ? EVAL.headline : "Run trust evaluation to produce a binding decision."}
        </p>
        {evaluated ? (
          <p className="mt-1.5 text-[13px] leading-5 text-muted-foreground">{EVAL.explanation}</p>
        ) : null}
        <div className="mt-5 flex gap-px bg-border">
          {[
            { k: "denials", v: denies, tone: "text-blocked" },
            { k: "evidence paths", v: evidenceCount, tone: "text-warning" },
            { k: "writeback ops", v: (WRITEBACK || []).length, tone: "text-metadata" },
          ].map((c) => (
            <div key={c.k} className="bg-surface px-5 py-2 text-center">
              <div className={`font-mono text-[20px] leading-tight font-semibold ${c.tone}`}>
                {evaluated ? c.v : "—"}
              </div>
              <div className="label-xs">{c.k}</div>
            </div>
          ))}
        </div>
        <p className="mt-4 font-mono text-[11px] leading-5 text-muted-foreground">
          <span className="text-foreground">evaluation_source</span> → {EVAL.evaluation_source || "not_evaluated"}
          {writebackAspects.length ? <> · {writebackAspects.join(" · ")}</> : null}
        </p>
        <dl className="mt-1.5 flex flex-wrap justify-center gap-x-5 gap-y-1 font-mono text-[11px] text-muted-foreground">
          <div><dt className="inline">mode=</dt><dd className="inline text-foreground">fail-closed</dd></div>
          <div><dt className="inline">policies_evaluated=</dt><dd className="inline text-foreground">{evaluated ? EVAL.policies_evaluated : "—"}</dd></div>
          <div><dt className="inline">latency=</dt><dd className="inline text-foreground">{evaluated ? `${EVAL.latency_ms}ms` : "—"}</dd></div>
          <div><dt className="inline">reason=</dt><dd className="inline text-foreground">{evaluated ? EVAL.reason_code || "—" : "—"}</dd></div>
          <div><dt className="inline">gms=</dt><dd className="inline text-foreground">{EVAL.gms_endpoint || "—"}</dd></div>
        </dl>
      </div>
    </div>
  );
}

/* ---------- 03 evidence: the decisive chain, read as a vertical proof ---------- */

function ProofStep({
  step,
  kind,
  children,
  last = false,
}: {
  step: string;
  kind: string;
  children: React.ReactNode;
  last?: boolean;
}) {
  return (
    <li className="relative grid grid-cols-[22px_minmax(0,1fr)] gap-x-3 pb-4 last:pb-0">
      <div className="relative flex justify-center">
        <span className="z-10 mt-1 h-2 w-2 shrink-0 border border-border-strong bg-surface-raised" />
        {last ? null : (
          <span aria-hidden className="absolute top-3 bottom-0 w-px bg-border-strong" />
        )}
      </div>
      <div className="min-w-0">
        <div className="label-xs">
          {step} · {kind}
        </div>
        <div className="mt-1 min-w-0">{children}</div>
      </div>
    </li>
  );
}


function DecisiveProof({ row, selected, onSelect }: { row: any; selected: boolean; onSelect: () => void; }) {
  if (!row) return null;
  const field = parseUrn(row.feature_urn || row.tainted_urn);


  return (
    <div
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
      className={`cursor-pointer border-l-2 px-4 py-4 text-left transition-colors ${
        selected ? "border-l-blocked bg-surface-raised" : "border-l-blocked/40 bg-surface hover:bg-surface-raised"
      }`}
    >
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-mono text-[11px] text-blocked">{row.id}</span>
        <span className="text-[14px] font-bold text-blocked uppercase tracking-wide">Determining chain</span>
        <span className="label-xs">first fatal deny · reducer terminates here</span>
      </div>

      <ol className="mt-3">
        <ProofStep step="01" kind="SchemaField">
          <div className="font-mono text-[13px] break-all text-foreground">{field.label}</div>
          <div className="mt-0.5 font-mono text-[11px] text-muted-foreground">
            {field.qualifier} · {row.confidence}
          </div>
        </ProofStep>
        <ProofStep step="02" kind="GlobalTag">
          <span className="inline-flex border border-warning/40 bg-warning-dim/25 px-1.5 py-0.5 font-mono text-[12px] text-warning">
            {row.tag_found}
          </span>
          <div className="mt-1 text-[12px] leading-5 text-muted-foreground">
            inherited through {row.transform || "IDENTITY" || "IDENTITY" || "IDENTITY"}
          </div>
        </ProofStep>
        <ProofStep step="03" kind="DataHubPolicy">
          <div className="text-[13px] text-foreground">{row.policy_id_id_id_id}</div>
          <div className="mt-0.5 font-mono text-[11px] text-muted-foreground">{row.policy_id_id_id}</div>
        </ProofStep>
        <ProofStep step="04" kind="Decision" last>
          <div className="flex flex-wrap items-center gap-2.5">
            <VerdictChip verdict={row.verdict} size="md" />
            <span className="text-[13px] text-foreground">{row.rationale}</span>
          </div>
          {row.rationale ? (
            <p className="mt-1 text-[12px] leading-5 text-muted-foreground">— {row.rationale}.</p>
          ) : null}
        </ProofStep>
      </ol>
    </div>
  );
}

/** Non-determining predicates: evaluated, retained, faded until selected. */
function SecondaryCheck({
  row,
  selected,
  onSelect,
}: {
  row: (typeof EVIDENCE)[number];
  selected: boolean;
  onSelect: () => void;
}) {
  const summary = EVIDENCE_SUMMARY[row.id];
  const field = parseUrn((row.feature_urn || row.tainted_urn));

  return (
    <li
      className={`border-l-2 transition-opacity ${
        selected
          ? "border-l-metadata bg-surface-raised opacity-100"
          : "border-l-transparent bg-surface opacity-45 hover:opacity-100 focus-within:opacity-100"
      }`}
    >
      <div
        role="button"
        tabIndex={0}
        aria-pressed={selected}
        onClick={onSelect}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onSelect();
          }
        }}
        className="cursor-pointer px-4 py-2.5 text-left transition-colors hover:bg-surface-raised"
      >
        <div className="flex min-w-0 flex-wrap items-center gap-x-2.5 gap-y-1">
          <span className="font-mono text-[11px] text-muted-foreground">{row.id}</span>
          <span className="max-w-[300px] truncate font-mono text-[12px]" title={field.label}>
            {field.label}
          </span>
          <Arrow />
          <span className="font-mono text-[11px] text-warning">{row.tag_found}</span>
          <Arrow />
          <span className="text-[12px] text-muted-foreground">
            {row.policy_id_id_id_id}
          </span>
          <Arrow />
          <VerdictChip verdict={row.verdict} />
        </div>
        <p className="mt-1 text-[12px] leading-5 text-muted-foreground">{row.rationale}</p>
      </div>
    </li>
  );
}



function NodeInspector({ id, payload }: { id: string; payload?: any }) {
  const node = INSPECTOR[id];
  if (!node) return null;
  const parsed = parseUrn(node.urn);
  
  const rows: Array<[string, React.ReactNode]> = [
    ["Entity", <span className="font-mono text-[12px]">{node.entityType}</span>],
    ["Name", <span className="font-mono text-[12px] break-all text-foreground">{parsed.label}</span>],
    ["Canonical URN", <UrnRef value={node.urn} showEntity={false} />],
    ["Description", <span className="text-[12px] leading-5 text-foreground">{node.description || "—"}</span>],
    ["Tags", <span className="flex flex-wrap gap-1">{(node.tags||[]).map((t: string) => (<span key={t} className="border border-border-strong bg-surface-raised px-1.5 py-0.5 font-mono text-[10px] text-warning">{t}</span>))}</span>],
    ["Glossary Terms", <span className="flex flex-wrap gap-1">{(node.glossaryTerms||[]).map((t: string) => (<span key={t} className="border border-border-strong bg-surface-raised px-1.5 py-0.5 font-mono text-[10px] text-metadata">{t}</span>))}</span>],
  ];

  return (
    <aside
      aria-label="DataHub entity"
      className="border-l border-border bg-surface lg:sticky lg:top-0 lg:max-h-screen lg:self-start lg:overflow-y-auto"
    >
      <div className="flex items-baseline gap-2 border-b border-border px-4 py-2">
        <h3 className="label-xs">Resolved DataHub Entity</h3>
        <span className="label-xs ml-auto">{id}</span>
      </div>
      <dl className="divide-y divide-border">
        {rows.map(([k, v]) => (
          <div key={k} className="px-4 py-2.5">
            <dt className="label-xs">{k}</dt>
            <dd className="mt-1 min-w-0">{v}</dd>
          </div>
        ))}
      </dl>
      <div className="border-y border-border bg-surface-raised px-4 py-2">
        <h4 className="label-xs">DataHub Aspect Trace</h4>
      </div>
      <dl className="divide-y divide-border">
        {node.evidence.map((ev, i) => (
          <div key={i} className="px-4 py-2.5">
            <dd className="mt-1 min-w-0 font-mono text-[11px] text-muted-foreground">{ev}</dd>
          </div>
        ))}
      </dl>
    </aside>
  );
}


/* ---------- tables ---------- */

function DataTable({ columns, children }: { columns: string[]; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="border-b border-border">
            {columns.map((c) => (
              <th key={c} scope="col" className="label-xs px-4 py-2 font-normal whitespace-nowrap">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">{children}</tbody>
      </table>
    </div>
  );
}

/* ---------- page ---------- */

const PRINCIPAL = "urn:li:corpuser:underwrite-ui";

export function UnderwriteConsole() {
  const [state, setState] = useState<"idle" | "running" | "done" | "error">("idle");
  const [rawUrns, setRawUrns] = useState(false);
  const [modelUrn, setModelUrn] = useState(
    "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
  );
  const [payload, setPayload] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [writebackStatus, setWritebackStatus] = useState<{ status: string; message: string } | null>(null);

  const evaluated = state === "done" && !!payload;
  const evalSource = payload?.evaluation_source || (state === "idle" ? "not_evaluated" : "unavailable");
  const request = payload?.request || {
    model_urn: modelUrn,
    environment: "PROD",
    action: "DEPLOY",
    requested_by: PRINCIPAL,
    request_id: "—",
    gms_endpoint: "—",
  };
  const evalBlock = {
    ...(payload?.evaluation || {}),
    evaluation_source: evalSource,
    action: request.action,
    environment: request.environment,
    gms_endpoint: request.gms_endpoint,
  };
  const evidence = (payload?.evidence_paths || []).map((ep: any, i: number) => ({
    id: `ev-${i}`,
    feature_urn: ep.feature_urn,
    tainted_urn: ep.tainted_urn,
    tag_found: ep.tag_found,
    policy_id: ep.policy_id,
    path: ep.path || [],
    rationale: ep.rationale || "",
    verdict: "BLOCKED" as Verdict,
    schemaFieldUrn: ep.feature_urn || "—",
    upstreamFieldUrn: ep.tainted_urn || "—",
    transform: "LINEAGE",
    globalTag: ep.tag_found || "—",
    aspect: "upstreamLineage",
  }));
  const decisive = evidence[0];
  const others = evidence.slice(1);
  const writeback = Array.isArray(payload?.write_back)
    ? payload.write_back
    : payload?.write_back
      ? [payload.write_back]
      : [];
  const events = payload?.execution_events || [];

  // Write-back is a background side effect, so its real outcome is only known
  // after the verdict has already been returned.
  const pollWriteback = async (requestId: string) => {
    for (let attempt = 0; attempt < 10; attempt++) {
      await new Promise((r) => setTimeout(r, 600));
      try {
        const res = await fetch(`/writeback/${requestId}`);
        if (!res.ok) return;
        const data = await res.json();
        setWritebackStatus({ status: data.status, message: data.message });
        if (data.status !== "PENDING") return;
      } catch {
        return;
      }
    }
  };

  const evaluate = async () => {
    setState("running");
    setError(null);
    setWritebackStatus(null);
    try {
      const res = await fetch("/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_urn: modelUrn, requested_by: PRINCIPAL }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || `HTTP ${res.status}`);
      }
      setPayload(data);
      setState("done");
      if (data?.request?.request_id && data?.evaluation_source === "live_datahub") {
        void pollWriteback(data.request.request_id);
      }
    } catch (e: any) {
      setPayload(null);
      setError(e?.message || "Evaluation failed");
      setState("error");
    }
  };

  return (
    <UrnModeContext.Provider value={rawUrns}>
      <div className="min-h-screen bg-background">
        <header className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-border bg-surface px-4 py-2.5">
          <span className="font-mono text-[13px] font-semibold tracking-tight">UNDERWRITE</span>
          <span aria-hidden className="text-border-strong">/</span>
          <span className="text-[12px] text-muted-foreground">Trust Runtime for DataHub</span>
          <label className="ml-auto flex items-center gap-2 font-mono text-[11px] text-muted-foreground">
            <input type="checkbox" checked={rawUrns} onChange={(e) => setRawUrns(e.target.checked)} />
            show raw URNs
          </label>
        </header>

        <HonestBanner />

        <Section index="01" title="Trust Evaluation Request" meta="admission control">
          <div className="bg-surface px-4 py-3 border-b border-border">
            <div className="flex items-center gap-3">
              <span className="label-xs whitespace-nowrap">Model URN:</span>
              <input
                type="text"
                className="flex-1 bg-background border border-border-strong px-2 py-1 text-[12px] font-mono text-foreground focus:outline-none focus:border-ring"
                value={modelUrn}
                onChange={(e) => setModelUrn(e.target.value)}
                disabled={state === "running"}
              />
            </div>
            {error ? (
              <p className="mt-2 font-mono text-[11px] text-blocked">{error}</p>
            ) : null}
          </div>
          <RequestBar onEvaluate={evaluate} state={state === "error" ? "idle" : state} request={request} evalSource={evalSource} />
        </Section>

        <Section index="02" title="Trust Decision" meta="deterministic fail-closed reducer">
          <DecisionBanner
            evaluated={evaluated}
            EVAL={evalBlock}
            WRITEBACK={writeback}
            evidenceCount={evidence.length}
          />
        </Section>

        <Section index="03" title="Verification Evidence" meta="from /evaluate evidence_paths">
          {decisive ? (
            <div className="bg-surface px-4 py-4 font-mono text-[12px] space-y-2">
              <div>
                <span className="text-muted-foreground">policy </span>
                {decisive.policy_id || "—"}
              </div>
              <div>
                <span className="text-muted-foreground">tainted </span>
                <UrnRef value={decisive.tainted_urn || "—"} showEntity={false} />
              </div>
              <div>
                <span className="text-muted-foreground">tag </span>
                {decisive.tag_found || "—"}
              </div>
              <div className="break-all text-muted-foreground">
                path: {(decisive.path || []).join(" → ")}
              </div>
              {decisive.rationale ? <div>{decisive.rationale}</div> : null}
              {others.length ? (
                <div className="pt-2 text-muted-foreground">{others.length} additional evidence path(s)</div>
              ) : null}
            </div>
          ) : (
            <div className="bg-surface px-4 py-6 font-mono text-[12px] text-muted-foreground">
              {!evaluated
                ? "No evidence yet. Evaluate against a live DataHub-backed API (GMS healthy) to populate this panel."
                : String(evalBlock.verdict || "").toLowerCase() === "approved"
                  ? `No policy violated. ${evalBlock.policies_evaluated ?? 0} policies were evaluated against the full lineage graph and none matched — an approval is the absence of evidence, not the absence of a check.`
                  : "Blocked without an evidence path. This is the fail-closed default: the graph could not be proven safe, so no approval is issued."}
            </div>
          )}
        </Section>

        <Section index="04" title="Lineage Graph" meta="serialized from evaluation graph">
          <div className="bg-[#0f172a] p-4 text-[11px] leading-[1.6]">
            <div className="mb-2 flex flex-wrap gap-4 font-mono text-[11px] text-[#94a3b8]">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-sm border-2 border-[#ef4444] bg-[#450a0a]" />
                on evidence path
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-sm border border-dashed border-[#f59e0b] bg-[#1c1917]" />
                unresolved upstream
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2.5 w-2.5 rounded-sm border border-[#334155] bg-[#1e293b]" />
                clean
              </span>
            </div>
            <GraphVisualizer nodes={payload?.graph?.nodes || []} edges={payload?.graph?.edges || []} />
          </div>
        </Section>

        <Section index="05" title="DataHub Write-Back" meta="side effect · never gates the verdict">
          <div className="bg-surface px-4 py-3">
            <div className="font-mono text-[11px] text-muted-foreground">
              status{" "}
              <span
                className={
                  writebackStatus?.status === "SUCCESS" || writebackStatus?.status === "SKIPPED"
                    ? "text-approved"
                    : writebackStatus?.status === "PENDING" || !writebackStatus
                      ? "text-muted-foreground"
                      : "text-warning"
                }
              >
                {evaluated ? writebackStatus?.status || "PENDING" : "—"}
              </span>
              {writebackStatus?.message ? (
                <span className="text-muted-foreground"> · {writebackStatus.message}</span>
              ) : null}
            </div>
            {writeback.length ? (
              <ul className="mt-2 divide-y divide-border font-mono text-[11px]">
                {writeback.map((w: any, i: number) => (
                  <li key={`${w.aspect}-${i}`} className="grid grid-cols-[90px_140px_minmax(0,1fr)] gap-3 py-1.5">
                    <span className="text-metadata">{w.operation}</span>
                    <span className="text-foreground">{w.aspect}</span>
                    <span className="break-all text-muted-foreground">
                      <UrnRef value={w.urn} showEntity={false} />
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 font-mono text-[11px] text-muted-foreground">
                No write-back operations planned for this decision.
              </p>
            )}
          </div>
        </Section>

        <Section index="06" title="Trust Trace" meta="deterministic · replayable">
          <ol className="divide-y divide-border">
            {events.length ? (
              events.map((e: any, idx: number) => (
                <li
                  key={`${e.timestamp || idx}-${e.stage}`}
                  className="grid grid-cols-[100px_110px_minmax(0,1fr)] gap-3 px-4 py-1.5 hover:bg-surface-raised"
                >
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {e.timestamp ? String(e.timestamp).split("T")[1]?.substring(0, 8) : ""}
                  </span>
                  <span className="font-mono text-[11px] text-metadata">{e.stage}</span>
                  <span className="font-mono text-[11px] break-all">{e.detail}</span>
                </li>
              ))
            ) : (
              <li className="px-4 py-3 font-mono text-[11px] text-muted-foreground">No execution events yet.</li>
            )}
          </ol>
        </Section>

        <footer className="px-4 py-3 font-mono text-[11px] text-muted-foreground">
          underwrite · evaluation_source must be live_datahub for CI approve · UI mirrors API only
        </footer>
      </div>
    </UrnModeContext.Provider>
  );
}

