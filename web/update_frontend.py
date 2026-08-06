import re
from pathlib import Path

console_path = Path("/Users/dhruv/.gemini/antigravity/scratch/underwrite/frontend/src/components/underwrite-console.tsx")
content = console_path.read_text()

# Remove the import from underwrite-data
content = re.sub(
    r'import \{[\s\S]*?\} from "@/lib/underwrite-data";',
    "",
    content
)
# And the type Verdict
content = re.sub(r'import type \{ Verdict \} from "@/lib/underwrite-data";', 'type Verdict = "BLOCKED" | "APPROVED" | "WARN";', content)

# In UnderwriteConsole component, add payload state and fetch logic.
console_decl = """export function UnderwriteConsole() {
  const [payload, setPayload] = useState<any>(null);
  const [modelUrn, setModelUrn] = useState("urn:li:mlModel:(urn:li:dataPlatform:mlflow,feed_ranking_v42,PROD)");
  const [state, setState] = useState<"idle" | "running" | "done">("idle");
  const [selected, setSelected] = useState<string>("");
  const [rawUrns, setRawUrns] = useState(false);
  const evaluated = state === "done" && payload !== null;

  const evaluate = async () => {
    setState("running");
    try {
      const res = await fetch("/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_urn: modelUrn, environment: "PROD", action: "DEPLOY / SERVING_ENDPOINT_PROMOTE", requested_by: "urn:li:corpuser:ml-platform-bot" })
      });
      const data = await res.json();
      setPayload(data);
      setState("done");
      if (data.evidence_paths && data.evidence_paths.length > 0) {
        setSelected(data.evidence_paths[0].id);
      }
    } catch (e) {
      console.error(e);
      setState("done");
    }
  };

  const REQUEST = payload?.request || { model_urn: modelUrn, environment: "PROD", action: "DEPLOY / SERVING_ENDPOINT_PROMOTE", requested_by: "urn:li:corpuser:ml-platform-bot", request_id: "—", gms_endpoint: "—" };
  const EVAL = payload?.evaluation || {};
  const EVIDENCE = payload?.evidence_paths || [];
  const WRITEBACK = payload?.write_back || [];
  const EXECUTION_EVENTS = payload?.execution_events || [];
  const EVAL_SOURCE = payload?.evaluation_source || "live_datahub";

  const decisive = EVIDENCE.find((e: any) => e.verdict === "BLOCKED") ?? EVIDENCE[0] ?? null;
  const others = EVIDENCE.filter((e: any) => e.id !== decisive?.id);

"""

content = re.sub(
    r'export function UnderwriteConsole\(\) \{[\s\S]*?const others = EVIDENCE\.filter\(\(e\) => e\.id !== decisive\.id\);[\s\S]*?const evaluate = \(\) => \{[\s\S]*?\}\);[\s\S]*?\};',
    console_decl,
    content
)

# Fix RequestBar
content = content.replace(
    'value={REQUEST.modelUrn}', 'value={REQUEST.model_urn}'
).replace(
    'REQUEST.requestedBy', 'REQUEST.requested_by'
).replace(
    'REQUEST.requestId', 'REQUEST.request_id'
).replace(
    'REQUEST.gmsEndpoint', 'REQUEST.gms_endpoint'
)

# Fix DecisionBanner
decision_banner_fixes = """
function DecisionBanner({ evaluated, EVAL, WRITEBACK }: { evaluated: boolean; EVAL: any; WRITEBACK: any[] }) {
  const denies = EVAL.denials ?? 0;
  const warns = EVAL.warnings ?? 0;
  const allows = EVAL.allowances ?? 0;
  const writebackAspects = Array.from(new Set(WRITEBACK.map((w) => w.aspect)));

"""
content = re.sub(
    r'function DecisionBanner\(\{ evaluated \}: \{ evaluated: boolean \}\) \{[\s\S]*?const writebackAspects = Array.from\(new Set\(WRITEBACK.map\(\(w\) => w.aspect\)\)\);',
    decision_banner_fixes,
    content
)

content = content.replace(
    '<DecisionBanner evaluated={evaluated} />',
    '<DecisionBanner evaluated={evaluated} EVAL={EVAL} WRITEBACK={WRITEBACK} />'
)

content = content.replace(
    'EVIDENCE.filter', '(EVIDENCE || []).filter'
)

content = content.replace(
    'DECISION_SUMMARY.headline', 'EVAL.headline'
).replace(
    'DECISION_SUMMARY.reason', 'EVAL.explanation'
).replace(
    'EVAL.policies_evaluated=', 'EVAL.policies_evaluated='
)

# Replace policies_evaluated hardcoded '4'
content = content.replace(
    '<dd className="inline text-foreground">4</dd>',
    '<dd className="inline text-foreground">{evaluated ? EVAL.policies_evaluated : "—"}</dd>'
)
# Replace latency hardcoded '96ms'
content = content.replace(
    '<dd className="inline text-foreground">{evaluated ? "96ms" : "—"}</dd>',
    '<dd className="inline text-foreground">{evaluated ? EVAL.latency_ms + "ms" : "—"}</dd>'
)


# Fix NodeInspector
node_inspector_fixes = """
function NodeInspector({ id, payload }: { id: string; payload: any }) {
  if (!payload || !payload.graph || !payload.graph.nodes) return null;
  const chain = (payload.evidence_paths || []).find((e: any) => e.id === id);
  const node = payload.graph.nodes.find((n: any) => n.id === (chain?.tainted_urn || id));
  if (!node) return null;
  const parsed = parseUrn(node.urn);
  
  const rows: Array<[string, React.ReactNode]> = [
    ["Entity", <span className="font-mono text-[12px]">{node.type}</span>],
    ["Name", <span className="font-mono text-[12px] break-all text-foreground">{parsed.label}</span>],
    ["Canonical URN", <UrnRef value={node.urn} showEntity={false} />],
    ["Description", <span className="text-[12px] leading-5 text-foreground">{node.description || "—"}</span>],
    ["Tags", <span className="flex flex-wrap gap-1">{(node.tags||[]).map((t: string) => (<span key={t} className="border border-border-strong bg-surface-raised px-1.5 py-0.5 font-mono text-[10px] text-warning">{t}</span>))}</span>],
    ["Glossary Terms", <span className="flex flex-wrap gap-1">{(node.glossaryTerms||[]).map((t: string) => (<span key={t} className="border border-border-strong bg-surface-raised px-1.5 py-0.5 font-mono text-[10px] text-metadata">{t}</span>))}</span>],
  ];

"""
content = re.sub(
    r'function NodeInspector\(\{ id \}: \{ id: string \}\) \{[\s\S]*?\];\s*/\* DataHub aspect trace',
    node_inspector_fixes + '  /* DataHub aspect trace',
    content
)

content = content.replace(
    '<NodeInspector id={selected} />',
    '<NodeInspector id={selected} payload={payload} />'
)

# Fix DecisiveProof
decisive_proof_fixes = """
function DecisiveProof({ row, selected, onSelect }: { row: any; selected: boolean; onSelect: () => void; }) {
  if (!row) return null;
  const field = parseUrn(row.feature_urn || row.tainted_urn);
"""
content = re.sub(
    r'function DecisiveProof\([\s\S]*?const field = parseUrn\(row\.schemaFieldUrn\);',
    decisive_proof_fixes,
    content
)

content = content.replace(
    'row.transform', 'row.transform || "IDENTITY"'
).replace(
    'summary?.policyTitle ?? row.policy', 'row.policy_id'
).replace(
    'summary?.headline', 'row.rationale'
).replace(
    'summary?.because ? (', 'row.rationale ? ('
).replace(
    'summary.because', 'row.rationale'
).replace(
    'row.policy', 'row.policy_id'
).replace(
    'row.schemaFieldUrn', '(row.feature_urn || row.tainted_urn)'
).replace(
    'row.upstreamFieldUrn', 'row.tainted_urn'
).replace(
    'row.tagUrn', 'row.tag_found'
).replace(
    'row.globalTag', 'row.tag_found'
).replace(
    'row.policyUrn', 'row.policy_id'
).replace(
    'summary?.policyTitle', 'row.policy_id'
)

# Fix SecondaryCheck
sec_check_fixes = """
function SecondaryCheck({ row, selected, onSelect }: { row: any; selected: boolean; onSelect: () => void; }) {
  if (!row) return null;
  const field = parseUrn(row.feature_urn || row.tainted_urn);
"""
content = re.sub(
    r'function SecondaryCheck\([\s\S]*?const field = parseUrn\(row\.schemaFieldUrn\);',
    sec_check_fixes,
    content
)


# Add an input box for the model URN right before the RequestBar
input_ui = """
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
               <button
                  type="button"
                  onClick={() => setRawUrns((v) => !v)}
                  aria-pressed={rawUrns}
                  className={`border px-2 py-1 font-mono text-[10px] tracking-[0.08em] uppercase transition-colors ${
                    rawUrns
                      ? "border-metadata/60 bg-metadata-dim/40 text-metadata"
                      : "border-border text-muted-foreground hover:border-ring hover:text-foreground"
                  }`}
                >
                  canonical urns {rawUrns ? "on" : "off"}
                </button>
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
"""
content = content.replace(
    '<RequestBar onEvaluate={evaluate} state={state} />',
    input_ui
)

console_path.write_text(content)
