/**
 * Underwrite — Lineage Graph Renderer
 *
 * Renders a DAG of lineage nodes and edges as SVG.
 * Includes interactive graph legend, path highlighting on click, hover tooltips, and bezier curves.
 * Zero external dependencies.
 */

const NODE_COLORS = {
  dataset:       '#3b82f6',
  transform:     '#8b5cf6',
  feature_table: '#06b6d4',
  feature:       '#14b8a6',
  schema_field:  '#a855f7',
  model:         '#f97316',
  deployment:    '#10b981',
  unknown:       '#64748b',
};

const NODE_TYPE_LABELS = {
  dataset:       'Dataset',
  transform:     'dbt Model',
  feature_table: 'Feature Table',
  feature:       'Feature',
  schema_field:  'Schema Field',
  model:         'ML Model',
  deployment:    'Deployment',
  unknown:       'Unknown',
};

const NODE_W = 154;
const NODE_H = 48;
const PAD = 24;

let activeSelectedNodeId = null;

function renderGraph(container, graphData) {
  container.innerHTML = '';
  activeSelectedNodeId = null;
  container.__underwriteGraphData = graphData;

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    container.innerHTML = '<div class="graph-empty">No lineage graph data available.</div>';
    return;
  }

  const nodes = graphData.nodes;
  const edges = graphData.edges || [];

  // Render Legend Header
  renderGraphToolbar(container, nodes);

  // Calculate SVG bounds
  const maxX = Math.max(...nodes.map((n) => n.x)) + NODE_W + PAD * 2;
  const maxY = Math.max(...nodes.map((n) => n.y)) + NODE_H + PAD * 2;

  const svgWrapper = document.createElement('div');
  svgWrapper.className = 'graph-svg-wrapper';

  const svg = createSvg('svg', {
    width: '100%',
    height: maxY + PAD,
    viewBox: `0 0 ${maxX} ${maxY}`,
    style: 'overflow: visible;',
    role: 'img',
    'aria-label': 'Lineage provenance graph showing data flow from sources through features to model',
  });

  // Node center lookup
  const centers = {};
  nodes.forEach((n) => {
    centers[n.id] = {
      cx: n.x + NODE_W / 2,
      cy: n.y + NODE_H / 2,
      top: n.y,
      bottom: n.y + NODE_H,
      left: n.x,
      right: n.x + NODE_W,
    };
  });

  // ─── Render Edges (behind nodes) ────────────────────────
  edges.forEach((edge) => {
    const from = centers[edge.from];
    const to = centers[edge.to];
    if (!from || !to) return;

    const dy = to.cy - from.cy;
    const dx = to.cx - from.cx;
    const isVertical = Math.abs(dy) > Math.abs(dx);

    let d;
    if (isVertical) {
      const startY = from.bottom;
      const endY = to.top;
      const ctrl = Math.min(Math.abs(endY - startY) * 0.4, 50);
      d = `M ${from.cx} ${startY} C ${from.cx} ${startY + ctrl}, ${to.cx} ${endY - ctrl}, ${to.cx} ${endY}`;
    } else {
      const goRight = to.cx > from.cx;
      const startX = goRight ? from.right : from.left;
      const endX = goRight ? to.left : to.right;
      const ctrl = Math.min(Math.abs(endX - startX) * 0.4, 50);
      d = `M ${startX} ${from.cy} C ${startX + (goRight ? ctrl : -ctrl)} ${from.cy}, ${endX + (goRight ? -ctrl : ctrl)} ${to.cy}, ${endX} ${to.cy}`;
    }

    let edgeClass = 'graph-edge';
    if (edge.isLeak) edgeClass += ' graph-edge--leak';
    else if (edge.isBroken) edgeClass += ' graph-edge--broken';

    const path = createSvg('path', {
      d,
      class: edgeClass,
      'data-from': edge.from,
      'data-to': edge.to,
    });
    svg.appendChild(path);

    // Arrowhead
    const arrowSize = 5;
    let ax, ay, angle;
    if (isVertical) {
      ax = to.cx;
      ay = to.top;
      angle = Math.PI / 2;
    } else {
      const goRight = to.cx > from.cx;
      ax = goRight ? to.left : to.right;
      ay = to.cy;
      angle = goRight ? 0 : Math.PI;
    }

    const p1 = `${ax + arrowSize * Math.cos(angle)},${ay + arrowSize * Math.sin(angle)}`;
    const p2 = `${ax - arrowSize * Math.cos(angle - Math.PI / 5)},${ay - arrowSize * Math.sin(angle - Math.PI / 5)}`;
    const p3 = `${ax - arrowSize * Math.cos(angle + Math.PI / 5)},${ay - arrowSize * Math.sin(angle + Math.PI / 5)}`;

    const arrow = createSvg('polygon', {
      points: `${p1} ${p2} ${p3}`,
      class: edge.isLeak ? 'graph-arrow graph-arrow--leak' : 'graph-arrow',
      'data-from': edge.from,
      'data-to': edge.to,
    });
    svg.appendChild(arrow);
  });

  // ─── Render Nodes ───────────────────────────────────────
  nodes.forEach((node) => {
    const color = NODE_COLORS[node.type] || NODE_COLORS.unknown;
    const isLeak = node.isLeakNode === true;

    const group = createSvg('g', {
      class: isLeak ? 'graph-node graph-node--leak' : 'graph-node',
      transform: `translate(${node.x}, ${node.y})`,
      'data-id': node.id,
      'data-label': node.label,
      'data-type': NODE_TYPE_LABELS[node.type] || node.type,
      tabindex: '0',
      role: 'button',
      'aria-pressed': 'false',
      'aria-label': `Node ${node.label}, type ${NODE_TYPE_LABELS[node.type] || node.type}${isLeak ? ', marked policy-relevant' : ''}`,
    });

    const rect = createSvg('rect', {
      width: NODE_W,
      height: NODE_H,
      rx: 8,
      ry: 8,
      fill: hexToRgba(color, 0.10),
      stroke: hexToRgba(color, 0.45),
      class: 'graph-node-rect',
    });
    group.appendChild(rect);

    const typeText = createSvg('text', {
      x: NODE_W / 2,
      y: 17,
      class: 'graph-node-type',
    });
    typeText.textContent = NODE_TYPE_LABELS[node.type] || node.type;
    group.appendChild(typeText);

    const nameText = createSvg('text', {
      x: NODE_W / 2,
      y: 35,
      class: 'graph-node-label',
    });
    const displayLabel = node.label.length > 18 ? node.label.slice(0, 16) + '…' : node.label;
    nameText.textContent = displayLabel;
    group.appendChild(nameText);

    // Event listeners
    group.addEventListener('mouseenter', (e) => showTooltip(container, node, e));
    group.addEventListener('mouseleave', () => hideTooltip(container));
    group.addEventListener('click', () => togglePathHighlight(container, graphData, node.id));
    group.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        togglePathHighlight(container, graphData, node.id);
      }
    });

    svg.appendChild(group);
  });

  svgWrapper.appendChild(svg);
  renderGraphInspector(container, graphData);
  container.appendChild(svgWrapper);
}

/* ─── Graph Toolbar & Legend ──────────────────────────────── */

function renderGraphToolbar(container, nodes) {
  const toolbar = document.createElement('div');
  toolbar.className = 'graph-toolbar';

  const legend = document.createElement('div');
  legend.className = 'graph-legend';

  // Extract unique types present
  const typesPresent = new Set(nodes.map((n) => n.type));
  if (nodes.some((n) => n.isLeakNode)) typesPresent.add('leak');

  typesPresent.forEach((type) => {
    const item = document.createElement('div');
    item.className = 'legend-item';

    const dot = document.createElement('span');
    dot.className = 'legend-dot';

    if (type === 'leak') {
      dot.style.background = 'var(--red)';
      dot.style.boxShadow = '0 0 6px var(--red)';
      item.appendChild(dot);
      item.appendChild(document.createTextNode('Matched provenance path'));
    } else {
      const color = NODE_COLORS[type] || NODE_COLORS.unknown;
      dot.style.background = color;
      item.appendChild(dot);
      item.appendChild(document.createTextNode(NODE_TYPE_LABELS[type] || type));
    }

    legend.appendChild(item);
  });

  const helpText = document.createElement('span');
  helpText.className = 'graph-help-text';
  helpText.textContent = 'Select a node to inspect provenance';

  toolbar.appendChild(legend);
  toolbar.appendChild(helpText);
  container.appendChild(toolbar);
}

/* ─── Node Inspector ─────────────────────────────────────── */

function renderGraphInspector(container, graphData, selectedId = null) {
  let inspector = container.querySelector('.graph-inspector');
  if (!inspector) {
    inspector = document.createElement('section');
    inspector.className = 'graph-inspector';
    inspector.setAttribute('aria-live', 'polite');
    container.appendChild(inspector);
  }

  const node = (graphData.nodes || []).find((item) => item.id === selectedId);
  if (!node) {
    inspector.innerHTML = '<div class="graph-inspector-empty"><strong>Provenance inspector</strong><span>Select a node to see its role in the deployment decision.</span></div>';
    return;
  }

  const policy = node.matched_policy || graphData.matched_policy;
  const tags = formatNodeTags(node.tags || node.global_tags || node.globalTags);
  const why = getNodeReason(node, graphData);
  const urn = node.urn || node.entity_urn || '';
  inspector.innerHTML = `
    <div class="graph-inspector-heading"><span>Selected node</span><strong>${escapeGraphText(node.label)}</strong></div>
    <dl class="graph-inspector-grid">
      <div><dt>Entity</dt><dd>${escapeGraphText(node.label)}</dd></div>
      <div><dt>Type</dt><dd>${escapeGraphText(NODE_TYPE_LABELS[node.type] || node.type)}</dd></div>
      <div class="graph-inspector-wide"><dt>URN</dt>${renderInspectorValue(urn, 'Unavailable in cached evaluation', 'Reconnect to DataHub to inspect canonical entity metadata.')}</div>
      <div><dt>Tags</dt>${renderInspectorValue(tags, 'Unavailable in cached evaluation', 'Tags are available during live DataHub evaluation.')}</div>
      <div><dt>Matched policy</dt>${renderInspectorValue(policy, 'Unavailable in cached evaluation', 'Policy bindings are available during live evaluation.')}</div>
      <div class="graph-inspector-wide"><dt>Why this node matters</dt><dd>${escapeGraphText(why)}</dd></div>
    </dl>`;
}

function getNodeReason(node, graphData) {
  if (node.isLeakNode) return 'This entity is on the evaluated provenance path.';
  const touchesLeak = (graphData.edges || []).some((edge) => (edge.from === node.id || edge.to === node.id) && edge.isLeak);
  if (touchesLeak) return 'This entity connects to the evaluated provenance path.';
  return 'This entity provides context for the resolved deployment lineage.';
}

function formatNodeTags(tags) {
  if (!tags) return '';
  if (Array.isArray(tags)) return tags.length ? tags.join(', ') : 'None';
  return String(tags);
}

function renderInspectorValue(value, unavailableLabel, unavailableNote) {
  if (value) return `<dd>${escapeGraphText(value)}</dd>`;
  return `<dd class="graph-inspector-unavailable"><span>${escapeGraphText(unavailableLabel)}</span><small>${escapeGraphText(unavailableNote)}</small></dd>`;
}

function escapeGraphText(value) {
  const element = document.createElement('div');
  element.textContent = value == null ? '' : String(value);
  return element.innerHTML;
}

/* ─── Path Highlighting Logic ────────────────────────────── */

function togglePathHighlight(container, graphData, selectedNodeId) {
  if (activeSelectedNodeId === selectedNodeId) {
    activeSelectedNodeId = null;
    resetPathHighlight(container);
    return;
  }

  activeSelectedNodeId = selectedNodeId;
  renderGraphInspector(container, graphData, selectedNodeId);

  // Find all upstream and downstream connected nodes
  const connectedNodes = new Set([selectedNodeId]);
  const connectedEdges = new Set();

  let queue = [selectedNodeId];
  while (queue.length > 0) {
    const curr = queue.shift();
    (graphData.edges || []).forEach((e) => {
      if (e.to === curr || e.from === curr) {
        connectedEdges.add(`${e.from}->${e.to}`);
        const neighbor = e.to === curr ? e.from : e.to;
        if (!connectedNodes.has(neighbor)) {
          connectedNodes.add(neighbor);
          queue.push(neighbor);
        }
      }
    });
  }

  // Update SVG DOM styles
  container.querySelectorAll('.graph-node').forEach((g) => {
    const id = g.getAttribute('data-id');
    g.setAttribute('aria-pressed', id === selectedNodeId ? 'true' : 'false');
    if (connectedNodes.has(id)) {
      g.classList.remove('is-dimmed');
      g.classList.add('is-active-path');
    } else {
      g.classList.add('is-dimmed');
      g.classList.remove('is-active-path');
    }
  });

  container.querySelectorAll('.graph-edge, .graph-arrow').forEach((el) => {
    const from = el.getAttribute('data-from');
    const to = el.getAttribute('data-to');
    if (connectedEdges.has(`${from}->${to}`)) {
      el.classList.remove('is-dimmed');
      el.classList.add('is-active-path');
    } else {
      el.classList.add('is-dimmed');
      el.classList.remove('is-active-path');
    }
  });
}

function resetPathHighlight(container) {
  container.querySelectorAll('.graph-node, .graph-edge, .graph-arrow').forEach((el) => {
    el.classList.remove('is-dimmed', 'is-active-path');
    if (el.classList.contains('graph-node')) el.setAttribute('aria-pressed', 'false');
  });
  const graphData = container.__underwriteGraphData;
  if (graphData) renderGraphInspector(container, graphData);
}

/* ─── Tooltip ──────────────────────────────────────────────── */

function showTooltip(container, node, event) {
  let tooltip = container.querySelector('.graph-tooltip');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.className = 'graph-tooltip';
    tooltip.setAttribute('aria-hidden', 'true');
    container.appendChild(tooltip);
  }

  const typeLabel = NODE_TYPE_LABELS[node.type] || node.type;
  const isLeakText = node.isLeakNode ? ' · TAINTED' : '';
  tooltip.textContent = `${node.label}  (${typeLabel}${isLeakText})`;
  tooltip.classList.add('is-visible');

  const rect = container.getBoundingClientRect();
  const x = event.clientX - rect.left + 12;
  const y = event.clientY - rect.top - 8;
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${y}px`;
}

function hideTooltip(container) {
  const tooltip = container.querySelector('.graph-tooltip');
  if (tooltip) tooltip.classList.remove('is-visible');
}

/* ─── SVG Helpers ──────────────────────────────────────────── */

function createSvg(tag, attrs) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attrs)) {
    el.setAttribute(key, value);
  }
  return el;
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
