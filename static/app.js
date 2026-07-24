/**
 * Underwrite — Application Controller
 *
 * State machine: idle → evaluating → verdict
 * Calls POST /evaluate, GET /health
 * Manages accordion, rendering, and error states.
 */
(() => {
  'use strict';

  /* ─── Constants ──────────────────────────────────────────── */

  const HEALTH_POLL_MS = 30000;

  const ICONS = {
    blocked: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    approved: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/></svg>',
    failed: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
  };

  /* ─── DOM References ─────────────────────────────────────── */

  const $ = (id) => document.getElementById(id);

  const el = {
    statusIndicator:  $('status-indicator'),
    statusText:       $('status-text'),
    modelSelect:      $('model-select'),
    evaluateBtn:      $('evaluate-btn'),
    evalBtnText:      $('eval-btn-text'),
    skeleton:         $('verdict-skeleton'),
    verdictSection:   $('verdict-section'),
    verdictHero:      $('verdict-hero'),
    verdictIcon:      $('verdict-icon'),
    verdictStatus:    $('verdict-status'),
    verdictHeadline:  $('verdict-headline'),
    verdictTimestamp:  $('verdict-timestamp'),
    summaryStatus:     $('summary-status'),
    summaryPolicy:     $('summary-policy'),
    summaryReason:     $('summary-reason'),
    summaryDepth:      $('summary-depth'),
    summarySource:     $('summary-source'),
    explanationText:  $('explanation-text'),
    evidencePaths:    $('evidence-paths'),
    graphContainer:   $('graph-container'),
    pipelineContent:  $('pipeline-content'),
    writebackContent: $('writeback-content'),
  };

  /* ─── State ──────────────────────────────────────────────── */

  let state = 'idle'; // 'idle' | 'evaluating' | 'verdict'

  /* ─── Health Check ───────────────────────────────────────── */

  async function checkHealth() {
    try {
      const res = await fetch('/health');
      const data = await res.json();
      if (data.datahub_gms === 'connected') {
        setStatus('live', 'DataHub: Connected');
      } else {
        setStatus('cached', 'DataHub: Cached');
      }
    } catch {
      setStatus('offline', 'DataHub: Offline');
    }
  }

  function setStatus(status, text) {
    el.statusIndicator.dataset.status = status;
    el.statusText.textContent = text;
  }

  /* ─── Evaluation ─────────────────────────────────────────── */

  async function evaluate() {
    if (state === 'evaluating') return;

    const modelUrn = el.modelSelect.value;
    transitionTo('evaluating');

    let result;
    try {
      const res = await fetch('/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_urn: modelUrn }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      result = await res.json();
    } catch {
      result = {
        verdict: 'blocked',
        reason_code: 'EVALUATION_FAILED',
        headline: 'Blocked — evaluation unavailable.',
        explanation: 'The policy engine did not return a verdict. Deployment remains blocked until the evaluation can be completed.',
      };
      result.model_urn = modelUrn;
      result.evaluated_at = new Date().toISOString();
    }

    transitionTo('verdict', result);
  }

  /* ─── State Transitions ──────────────────────────────────── */

  function transitionTo(newState, data) {
    state = newState;

    switch (newState) {
      case 'evaluating':
        el.evaluateBtn.className = 'eval-btn eval-btn--loading';
        el.evalBtnText.textContent = 'Evaluating…';
        el.verdictSection.classList.remove('is-visible');
        el.verdictSection.setAttribute('aria-hidden', 'true');
        el.skeleton.classList.add('is-visible');
        el.skeleton.setAttribute('aria-hidden', 'false');
        closeAllAccordions();
        break;

      case 'verdict':
        el.skeleton.classList.remove('is-visible');
        el.skeleton.setAttribute('aria-hidden', 'true');
        renderVerdict(data);
        el.verdictSection.classList.add('is-visible');
        el.verdictSection.setAttribute('aria-hidden', 'false');

        if (data.verdict === 'blocked') {
          el.evaluateBtn.className = 'eval-btn';
          el.evalBtnText.textContent = 'Evaluate again';
          // Surface both the proof and its lineage context for an unsafe decision.
          openAccordion($('trigger-why'));
          openAccordion($('trigger-graph'));
        } else {
          el.evaluateBtn.className = 'eval-btn';
          el.evalBtnText.textContent = 'Evaluate again';
          openAccordion($('trigger-graph'));
        }
        break;

      default: // idle
        el.evaluateBtn.className = 'eval-btn';
        el.evalBtnText.textContent = 'Evaluate deployment';
        el.verdictSection.classList.remove('is-visible');
        el.verdictSection.setAttribute('aria-hidden', 'true');
        el.skeleton.classList.remove('is-visible');
        el.skeleton.setAttribute('aria-hidden', 'true');
        break;
    }
  }

  /* ─── Verdict Rendering ──────────────────────────────────── */

  function renderVerdict(result) {
    const isFailed = result.verdict === 'failed' || result.reason_code === 'EVALUATION_FAILED';
    const isBlocked = !isFailed && result.verdict === 'blocked';

    // Hero
    if (isFailed) {
      el.verdictHero.className = 'verdict-hero verdict-hero--failed';
      el.verdictIcon.innerHTML = ICONS.failed;
      el.verdictStatus.textContent = 'EVALUATION FAILED';
    } else if (isBlocked) {
      el.verdictHero.className = 'verdict-hero verdict-hero--blocked';
      el.verdictIcon.innerHTML = ICONS.blocked;
      el.verdictStatus.textContent = 'BLOCKED';
    } else {
      el.verdictHero.className = 'verdict-hero verdict-hero--approved';
      el.verdictIcon.innerHTML = ICONS.approved;
      el.verdictStatus.textContent = 'APPROVED';
    }

    el.verdictHeadline.textContent = result.headline || (isFailed ? 'Evaluation engine failed.' : isBlocked ? 'Deployment blocked.' : 'Deployment approved.');

    // Decision summary — the primary question is answered without expanding evidence.
    const policyId = extractPolicyId(result);
    const evidencePath = result.evidence_paths && result.evidence_paths[0];
    const lineagePath = evidencePath && evidencePath.path ? evidencePath.path : [];
    const source = evidencePath && evidencePath.tainted_urn
      ? extractShortName(evidencePath.tainted_urn)
      : getSourceDataset(result.graph);
    el.summaryStatus.textContent = isFailed ? 'Evaluation failed' : isBlocked ? 'Blocked' : 'Approved';
    el.summaryPolicy.textContent = policyId || 'Not available from current payload';
    el.summaryReason.textContent = result.reason_code || 'Not available from current payload';
    el.summaryDepth.textContent = lineagePath.length ? `${Math.max(0, lineagePath.length - 1)} hops` : getTraversalDepth(result.execution_events, result.graph);
    el.summarySource.textContent = source || 'Not available from current payload';

    // Timestamp
    const sourceLabel = {
      live_datahub: 'Source: live DataHub',
      cached_fixture: 'Source: bundled cached fixture',
      unavailable: 'Source: evaluation unavailable',
    }[result.evaluation_source] || 'Source: unknown';
    el.verdictTimestamp.textContent = `${sourceLabel} · ${formatTimestamp(result.evaluated_at)}`;

    // Explanation panel
    renderExplanation(result.explanation, result.verdict);
    renderEvidencePaths(result.evidence_paths);

    // Graph panel
    if (result.graph && typeof renderGraph === 'function') {
      renderGraph(el.graphContainer, result.graph);
    } else {
      el.graphContainer.innerHTML = '<div class="graph-empty">No lineage graph data available.</div>';
    }

    // Pipeline panel
    renderPipeline(result.execution_events);

    // Write-back panel
    renderWriteback(result.write_back);
  }

  function extractPolicyId(result) {
    if (result.evidence_paths && result.evidence_paths.length > 0) {
      const firstPath = result.evidence_paths[0];
      if (firstPath.policy_id) return firstPath.policy_id;
    }
    return '';
  }

  /* ─── Evidence Paths ─────────────────────────────────────── */

  function renderEvidencePaths(paths) {
    el.evidencePaths.innerHTML = '';
    if (!paths || paths.length === 0) return;

    paths.forEach((ep) => {
      const container = document.createElement('div');
      container.className = 'evidence-path';

      const label = document.createElement('div');
      label.className = 'evidence-path-label';
      label.textContent = 'Evidence Path';
      container.appendChild(label);

      if (ep.path && ep.path.length > 0) {
        const chain = document.createElement('div');
        chain.className = 'evidence-chain';

        ep.path.forEach((urnStr, i) => {
          if (i > 0) {
            const arrow = document.createElement('span');
            arrow.className = 'chain-arrow';
            arrow.textContent = '→';
            arrow.setAttribute('aria-hidden', 'true');
            chain.appendChild(arrow);
          }

          const node = document.createElement('span');
          const shortName = extractShortName(urnStr);
          const isTainted = ep.tainted_urn && urnStr.includes(extractShortName(ep.tainted_urn));
          node.className = isTainted ? 'chain-node chain-node--tainted' : 'chain-node';
          node.textContent = shortName;
          chain.appendChild(node);
        });

        container.appendChild(chain);
      }

      if (ep.tag_found) {
        const tagEl = document.createElement('div');
        tagEl.className = 'chain-tag';
        tagEl.innerHTML = `<span aria-hidden="true">⚠</span> Tag: ${escapeHtml(ep.tag_found)}`;
        container.appendChild(tagEl);
      }

      el.evidencePaths.appendChild(container);
    });
  }

  function renderExplanation(explanation, verdict) {
    el.explanationText.innerHTML = '';
    if (!explanation) return;

    const sentences = explanation.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [explanation];
    const sections = [];
    if (sentences.length === 1) {
      sections.push(['Evidence', sentences[0]]);
    } else {
      sections.push(['Summary', sentences[0]]);
      if (sentences.length > 2) sections.push(['Evidence', sentences.slice(1, -1).join(' ')]);
      sections.push([verdict === 'approved' ? 'Decision basis' : 'Impact', sentences[sentences.length - 1]]);
    }

    sections.forEach(([label, text]) => {
      const section = document.createElement('div');
      section.className = 'evidence-brief';
      const heading = document.createElement('span');
      heading.textContent = label;
      const body = document.createElement('p');
      body.textContent = text.trim();
      section.append(heading, body);
      el.explanationText.appendChild(section);
    });
  }

  /* ─── Execution Pipeline ─────────────────────────────────── */

  function renderPipeline(events) {
    const container = el.pipelineContent;
    container.innerHTML = '';

    if (!events || events.length === 0) {
      container.innerHTML = '<div class="empty-state">Pipeline trace not available.</div>';
      return;
    }

    const timeline = document.createElement('div');
    timeline.className = 'timeline';

    events.forEach((ev, i) => {
      const step = document.createElement('div');
      const stageClass = getStageClass(ev.stage, ev.detail);
      step.className = `timeline-step ${stageClass}`;

      const rail = document.createElement('div');
      rail.className = 'timeline-rail';

      const dot = document.createElement('div');
      dot.className = 'timeline-dot';
      rail.appendChild(dot);

      if (i < events.length - 1) {
        const line = document.createElement('div');
        line.className = 'timeline-line';
        rail.appendChild(line);
      }

      const body = document.createElement('div');
      body.className = 'timeline-body';

      const stage = document.createElement('div');
      stage.className = 'timeline-stage';
      stage.textContent = ev.stage || `Step ${ev.step_num}`;
      body.appendChild(stage);

      const detail = document.createElement('div');
      detail.className = 'timeline-detail';
      detail.textContent = ev.detail || '';
      body.appendChild(detail);

      step.appendChild(rail);
      step.appendChild(body);
      timeline.appendChild(step);
    });

    container.appendChild(timeline);
  }

  function getStageClass(stage, detail) {
    if (!stage && !detail) return '';
    const text = ((stage || '') + ' ' + (detail || '')).toLowerCase();
    if (text.includes('blocked') || text.includes('leakage') || text.includes('matched') || text.includes('fail') || text.includes('incomplete')) {
      return 'timeline-step--alert';
    }
    if (text.includes('approved') || text.includes('clean') || text.includes('complete') || text.includes('persist')) {
      return 'timeline-step--success';
    }
    return 'timeline-step--info';
  }

  /* ─── Write-Back ─────────────────────────────────────────── */

  function renderWriteback(wb) {
    const container = el.writebackContent;
    container.innerHTML = '';

    if (!wb) {
      container.innerHTML = '<div class="empty-state">Write-back data not available.</div>';
      return;
    }

    const list = document.createElement('div');
    list.className = 'writeback-list';

    if (wb.tag) {
      list.appendChild(createWritebackItem('MLModel', 'GlobalTags', `urn:li:tag:${wb.tag}`, 'UPSERT', 'REQUESTED'));
    }

    if (wb.incident !== undefined) {
      const aspectVal = wb.incident ? 'IncidentInfo created on source' : 'IncidentInfo skipped (clean)';
      const status = wb.incident ? 'REQUESTED' : 'SKIPPED';
      list.appendChild(createWritebackItem('Source dataset', 'IncidentInfo', aspectVal, wb.incident ? 'UPSERT' : 'NO-OP', status));
    }

    if (wb.text) {
      list.appendChild(createWritebackItem('MLModel', 'InstitutionalMemory', wb.text, 'UPSERT', 'REQUESTED'));
    }

    container.appendChild(list);
  }

  function createWritebackItem(entity, aspect, value, operation, status) {
    const item = document.createElement('div');
    item.className = 'writeback-item';
    item.innerHTML = `
      <div class="writeback-operation"><span>Entity</span><strong>${escapeHtml(entity)}</strong></div>
      <div class="writeback-operation"><span>Aspect</span><strong>${escapeHtml(aspect)}</strong></div>
      <div class="writeback-operation writeback-operation--value"><span>Operation</span><strong>${escapeHtml(operation)} · ${escapeHtml(value)}</strong></div>
      <span class="writeback-status${status === 'SKIPPED' ? ' writeback-status--skipped' : ''}">${escapeHtml(status)}</span>
    `;
    return item;
  }

  function getSourceDataset(graph) {
    if (!graph || !graph.nodes) return '';
    const datasets = graph.nodes.filter((node) => (node.type === 'dataset' || node.type === 'unknown') && node.isLeakNode);
    if (datasets.length) return datasets[0].label;
    const allDatasets = graph.nodes.filter((node) => node.type === 'dataset' || node.type === 'unknown');
    return allDatasets.length ? allDatasets[0].label : '';
  }

  function getTraversalDepth(events, graph) {
    const traversal = (events || []).find((event) => (event.stage || '').toLowerCase() === 'traversal');
    const match = traversal && (traversal.detail || '').match(/\((\d+) hops?\)/i);
    if (match) return `${match[1]} hops`;
    if (!graph || !graph.nodes || !graph.edges) return 'Not available from current payload';
    const model = graph.nodes.find((node) => node.type === 'model');
    if (!model) return 'Not available from current payload';
    const incoming = new Map();
    graph.edges.forEach((edge) => incoming.set(edge.to, [...(incoming.get(edge.to) || []), edge.from]));
    const visit = (id, seen = new Set()) => {
      if (seen.has(id)) return 0;
      const parents = incoming.get(id) || [];
      return parents.length ? 1 + Math.max(...parents.map((parent) => visit(parent, new Set([...seen, id])))) : 0;
    };
    const hops = visit(model.id);
    return hops ? `${hops} hops` : 'Not available from current payload';
  }

  /* ─── Accordion ──────────────────────────────────────────── */

  function initAccordion() {
    document.querySelectorAll('.accordion-trigger').forEach((trigger) => {
      trigger.addEventListener('click', () => toggleAccordion(trigger));
    });
  }

  function toggleAccordion(trigger) {
    const item = trigger.closest('.accordion-item');
    const isOpen = item.classList.contains('is-open');

    if (isOpen) {
      closeAccordion(trigger);
    } else {
      openAccordion(trigger);
    }
  }

  function openAccordion(trigger) {
    const item = trigger.closest('.accordion-item');
    item.classList.add('is-open');
    trigger.setAttribute('aria-expanded', 'true');
  }

  function closeAccordion(trigger) {
    const item = trigger.closest('.accordion-item');
    item.classList.remove('is-open');
    trigger.setAttribute('aria-expanded', 'false');
  }

  function closeAllAccordions() {
    document.querySelectorAll('.accordion-trigger').forEach((trigger) => {
      closeAccordion(trigger);
    });
  }

  /* ─── Utilities ──────────────────────────────────────────── */

  function formatTimestamp(iso) {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      return d.toLocaleString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: 'numeric', minute: '2-digit', hour12: true,
      });
    } catch {
      return iso;
    }
  }

  function extractShortName(urn) {
    if (!urn) return '';
    // Extract the meaningful part from DataHub URN strings
    const parts = urn.split(',');
    if (parts.length >= 2) return parts[parts.length - 2].trim();
    const lastParen = urn.lastIndexOf('(');
    if (lastParen >= 0) return urn.slice(lastParen + 1).replace(/[)]/g, '').trim();
    return urn.split(':').pop() || urn;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /* ─── Init ───────────────────────────────────────────────── */

  function init() {
    // Health check on load + periodic refresh
    checkHealth();
    setInterval(checkHealth, HEALTH_POLL_MS);

    // Evaluate button
    el.evaluateBtn.addEventListener('click', evaluate);

    // Reset button state when model selection changes
    el.modelSelect.addEventListener('change', () => {
      if (state === 'verdict') {
        transitionTo('idle');
      }
    });

    // Accordion
    initAccordion();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
