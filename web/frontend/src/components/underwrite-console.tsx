

import { parseUrn } from "@/lib/urn";
import { useState, createContext, useContext } from "react";
import { Verdict, REQUEST, EVIDENCE, WRITEBACK, EXECUTION_EVENTS, EVIDENCE_SUMMARY, DECISION_SUMMARY, INSPECTOR } from "@/lib/underwrite-data";
import GraphVisualizer from "./GraphVisualizer";

const EVAL = {
  denials: 2,
  warnings: 1,
  allowances: 1,
  headline: DECISION_SUMMARY.headline,
  explanation: DECISION_SUMMARY.reason,
  policies_evaluated: 4,
  latency_ms: 96,
};

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
}: {
  onEvaluate: () => void;
  state: "idle" | "running" | "done";
}) {
  return (
    <div className="grid grid-cols-1 gap-px bg-border lg:grid-cols-[1fr_auto]">
      <dl className="grid grid-cols-1 gap-px bg-border sm:grid-cols-2 xl:grid-cols-4">
        <div className="bg-surface px-4 py-2.5">
          <dt className="label-xs">Subject</dt>
          <dd className="mt-1">
            <UrnRef value={REQUEST.model_urn} showEntity={false} />
          </dd>
        </div>
        <div className="bg-surface px-4 py-2.5">
          <dt className="label-xs">Target Environment</dt>
          <dd className="mt-1 font-mono text-[12px]">{REQUEST.environment}</dd>
        </div>
        <div className="bg-surface px-4 py-2.5">
          <dt className="label-xs">Requested Operation</dt>
          <dd className="mt-1 font-mono text-[12px]">{REQUEST.action}</dd>
        </div>
        <div className="bg-surface px-4 py-2.5">
          <dt className="label-xs">Principal</dt>
          <dd className="mt-1">
            <UrnRef value={REQUEST.requested_by} showEntity={false} />
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
        <span className="label-xs whitespace-nowrap">{REQUEST.request_id}</span>
        
        {/* Offline Demo / Live DataHub Badge */}
        <span className="ml-auto inline-flex items-center px-2 py-1 text-[11px] font-mono border border-metadata text-metadata bg-metadata/10 rounded">
          ✓ Live DataHub Connected
        </span>
      </div>
    </div>
  );
}

function GlobalStatsPanel() {
  return (
    <div className="bg-surface border-y border-border px-4 py-3 grid grid-cols-2 md:grid-cols-6 gap-4 text-center">
      <div><div className="font-mono text-[16px] text-foreground">4,381</div><div className="text-[10px] text-muted-foreground uppercase">Assets</div></div>
      <div><div className="font-mono text-[16px] text-foreground">247</div><div className="text-[10px] text-muted-foreground uppercase">Policies</div></div>
      <div><div className="font-mono text-[16px] text-warning">42</div><div className="text-[10px] text-muted-foreground uppercase">Critical Assets</div></div>
      <div><div className="font-mono text-[16px] text-metadata">91 ms</div><div className="text-[10px] text-muted-foreground uppercase">Traversal</div></div>
      <div><div className="font-mono text-[16px] text-metadata">38 ms</div><div className="text-[10px] text-muted-foreground uppercase">Evaluation</div></div>
      <div><div className="font-mono text-[16px] text-blocked font-bold">94</div><div className="text-[10px] text-muted-foreground uppercase">Risk Score</div></div>
    </div>
  );
}

/* ---------- 02 decision ---------- */


function DecisionBanner({ evaluated, EVAL, WRITEBACK }: { evaluated: boolean; EVAL: any; WRITEBACK: any[] }) {
  const denies = EVAL.denials ?? 0;
  const warns = EVAL.warnings ?? 0;
  const allows = EVAL.allowances ?? 0;
  const writebackAspects = Array.from(new Set(WRITEBACK.map((w) => w.aspect)));



  return (
    <div
      role="status"
      aria-live="polite"
      className={`border-l-2 px-4 py-8 ${
        evaluated ? "border-l-blocked bg-blocked-dim/25" : "border-l-border-strong bg-surface"
      }`}
    >
      <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
        <span className="label-xs">
          {REQUEST.action} · {REQUEST.environment}
        </span>
        <span
          className={`mt-2 font-mono text-[80px] leading-none font-bold tracking-tight ${
            evaluated ? "text-blocked animate-in fade-in duration-300" : "text-muted-foreground"
          }`}
        >
          {evaluated ? "BLOCKED" : "NOT EVALUATED"}
        </span>
        <p className="mt-3 text-[17px] font-medium text-foreground">
          {evaluated ? EVAL.headline : "Run trust evaluation to produce a binding decision."}
        </p>
        {evaluated ? (
          <p className="mt-1.5 text-[13px] leading-5 text-muted-foreground">
            {EVAL.explanation}
          </p>
        ) : null}

        <div className="mt-5 flex gap-px bg-border">
          {[
            { k: "denials", v: denies, tone: "text-blocked" },
            { k: "warnings", v: warns, tone: "text-warning" },
            { k: "allowances", v: allows, tone: "text-approved" },
            { k: "mutations staged", v: WRITEBACK.length, tone: "text-metadata" },
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
          <span className="text-foreground">metadata mutation on commit</span> → {writebackAspects.join(" · ")}{" "}
          <span className="text-warning">(staged, not committed)</span>
        </p>
        <dl className="mt-1.5 flex flex-wrap justify-center gap-x-5 gap-y-1 font-mono text-[11px] text-muted-foreground">
          <div>
            <dt className="inline">mode=</dt>
            <dd className="inline text-foreground">fail-closed</dd>
          </div>
          <div>
            <dt className="inline">policies_evaluated=</dt>
            <dd className="inline text-foreground">{evaluated ? EVAL.policies_evaluated : "—"}</dd>
          </div>
          <div>
            <dt className="inline">latency=</dt>
            <dd className="inline text-foreground">{evaluated ? EVAL.latency_ms + "ms" : "—"}</dd>
          </div>
          <div>
            <dt className="inline">gms=</dt>
            <dd className="inline text-foreground">{REQUEST.gms_endpoint}</dd>
          </div>
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

export function UnderwriteConsole() {
  const [state, setState] = useState<"idle" | "running" | "done">("done");
  const [selected, setSelected] = useState<string>("ev-01");
  const [rawUrns, setRawUrns] = useState(false);
  const [modelUrn, setModelUrn] = useState("urn:li:mlModel:(urn:li:dataPlatform:mlflow,feed_ranking_v42,PROD)");
  const EVAL_SOURCE = "cached_fixture";
  const payload = undefined;
  const evaluated = state === "done";
  const decisive = EVIDENCE.find((e) => e.verdict === "BLOCKED") ?? EVIDENCE[0]!;
  const others = (EVIDENCE || []).filter((e) => e.id !== decisive.id);

  const evaluate = () => {
    setState("running");
    window.setTimeout(() => setState("done"), 550);
  };

  return (
    <UrnModeContext.Provider value={rawUrns}>
      <div className="min-h-screen bg-background">
        <header className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-border bg-surface px-4 py-2.5">
          <span className="font-mono text-[13px] font-semibold tracking-tight">UNDERWRITE</span>
          <span aria-hidden className="text-border-strong">
            /
          </span>
          <span className="text-[12px] text-muted-foreground">Trust Runtime for DataHub</span>
          <div className="ml-auto flex items-center gap-3">
            <span className="font-mono text-[11px] text-muted-foreground">
              datahub-gms v0.14.1 · policy-set 2026.07.3
            </span>
          </div>
        </header>

        <GlobalStatsPanel />

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
               <span className={`border px-2 py-1 font-mono text-[10px] tracking-[0.08em] uppercase ${
                  EVAL_SOURCE === "cached_fixture"
                    ? "border-warning/60 bg-warning-dim/40 text-warning"
                    : "border-border text-muted-foreground"
                }`}>
                  {EVAL_SOURCE === "cached_fixture" ? "DataHub: Cached Mode" : "DataHub: Live Mode"}
                </span>
                <span className="font-mono text-[11px] text-muted-foreground">
                  datahub-gms v0.14.1 · policy-set 2026.07.3
                </span>
             </div>
          </div>
          <RequestBar onEvaluate={evaluate} state={state} />



        </Section>

        <Section index="02" title="Trust Decision" meta="deterministic fail-closed reducer">
          <DecisionBanner evaluated={evaluated} EVAL={EVAL} WRITEBACK={WRITEBACK} />
        </Section>

        <Section
          index="03"
          title="Verification Evidence"
          meta="schemaField → globalTag → policy → decision"
        >
          <div className="grid grid-cols-1 bg-surface lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
            <div>
              <DecisiveProof
                row={decisive}
                selected={selected === decisive.id}
                onSelect={() => setSelected(decisive.id)}
              />
              <div className="flex items-baseline gap-3 border-y border-border bg-surface px-4 py-1.5">
                <span className="label-xs">Non-determining predicates</span>
                <span className="label-xs ml-auto">evaluated · did not determine the verdict</span>
              </div>
              <ol className="divide-y divide-border bg-surface">
                {others.map((row) => (
                  <SecondaryCheck
                    key={row.id}
                    row={row}
                    selected={selected === row.id}
                    onSelect={() => setSelected(row.id)}
                  />
                ))}
              </ol>
            </div>
            <NodeInspector id={selected} payload={payload} />
          </div>
        </Section>

        <Section index="04" title="FineGrainedLineage" meta="column-level · depth 4 · 42 edges">
          <DataTable columns={["#", "Downstream Field", "Upstream Field", "Transform", "Tag", "Verdict"]}>
            {EVIDENCE.map((e, i) => (
              <tr key={e.id} className="align-top hover:bg-surface-raised">
                <td className="px-4 py-2 font-mono text-[11px] text-muted-foreground">
                  {String(i + 1).padStart(2, "0")}
                </td>
                <td className="w-[24%] px-4 py-2 pr-8">
                  <UrnRef value={e.schemaFieldUrn} showEntity={false} />
                </td>
                <td className="w-[24%] px-4 py-2 pr-8">
                  <UrnRef value={e.upstreamFieldUrn} showEntity={false} />
                </td>
                <td className="px-4 py-2 font-mono text-[11px] whitespace-nowrap">{e.transform}</td>
                <td className="px-4 py-2 font-mono text-[11px] whitespace-nowrap text-warning">
                  {e.globalTag}
                </td>
                <td className="px-4 py-2">
                  <VerdictChip verdict={e.verdict} />
                </td>
              </tr>
            ))}
          </DataTable>
        </Section>
        <Section index="05" title="Lineage Graph Visualizer" meta="column-level · depth 4 · react-flow">
          <div className="bg-[#0f172a] p-4 text-[11px] leading-[1.6]">
            <GraphVisualizer />
          </div>
        </Section>



        <Section
          index="05"
          title="Metadata Mutation"
          meta="MetadataChangeProposal · staged, not committed"
        >
          <DataTable columns={["Entity", "Target", "Aspect", "Operation", "Status"]}>
            {WRITEBACK.map((w) => (
              <tr key={`${w.entity}.${w.aspect}`} className="align-top hover:bg-surface-raised">
                <td className="px-4 py-2 font-mono text-[11px] whitespace-nowrap">{w.entity}</td>
                <td className="max-w-[260px] px-4 py-2">
                  <UrnRef value={w.urn} showEntity={false} />
                </td>
                <td className="px-4 py-2 font-mono text-[11px] whitespace-nowrap text-metadata">
                  {w.aspect}
                </td>
                <td className="px-4 py-2 font-mono text-[11px]">{w.operation}</td>
                <td className="px-4 py-2 whitespace-nowrap">
                  <StatusText value={w.status} />
                </td>
              </tr>
            ))}
          </DataTable>
        </Section>

        <Section index="06" title="Trust Trace" meta="deterministic · replayable">
          <ol className="divide-y divide-border">
            {EXECUTION_EVENTS.map((e) => (
              <li
                key={e.timestamp}
                className="grid grid-cols-[100px_110px_minmax(0,1fr)] gap-3 px-4 py-1.5 hover:bg-surface-raised"
              >
                <span className="font-mono text-[11px] text-muted-foreground">
                  {e.timestamp ? e.timestamp.split("T")[1]?.substring(0, 8) : ""}
                </span>
                <span className="font-mono text-[11px] text-metadata">{e.stage}</span>
                <span className="font-mono text-[11px] break-all">{e.detail}</span>
              </li>
            ))}
          </ol>
        </Section>



        <footer className="px-4 py-3 font-mono text-[11px] text-muted-foreground">
          underwrite trust runtime · request {REQUEST.request_id} · verdict is binding at
          admission; metadata mutations remain staged until committed to DataHub GMS
        </footer>
      </div>
    </UrnModeContext.Provider>
  );
}
