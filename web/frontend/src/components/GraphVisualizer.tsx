import { useState, useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';

const initialNodes = [
  { id: '1', position: { x: 50, y: 50 }, data: { label: 'raw.customers (Dataset)' }, style: { background: '#fff', border: '1px solid #777' } },
  { id: '2', position: { x: 50, y: 150 }, data: { label: 'customer_status (Column)' }, style: { background: '#fff', border: '1px solid #777' } },
  { id: '3', position: { x: 300, y: 150 }, data: { label: 'analytics.customer_summary (Table)' }, style: { background: '#fff', border: '1px solid #777' } },
  { id: '4', position: { x: 550, y: 100 }, data: { label: 'Dashboard: Revenue KPI' }, style: { background: '#fff', border: '1px solid #777' } },
  { id: '5', position: { x: 550, y: 200 }, data: { label: 'ML Model: Churn Predictor' }, style: { background: '#fff', border: '1px solid #777' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: false },
  { id: 'e2-3', source: '2', target: '3', animated: false },
  { id: 'e3-4', source: '3', target: '4', animated: false },
  { id: 'e3-5', source: '3', target: '5', animated: false },
];

export default function GraphVisualizer() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [timeTravel, setTimeTravel] = useState(false);

  const toggleTimeTravel = () => {
    setTimeTravel(!timeTravel);
    if (!timeTravel) {
      // Simulate "After PR"
      setEdges((eds) =>
        eds.map((edge) => {
          if (edge.id === 'e2-3') {
            return {
              ...edge,
              style: { stroke: 'red', strokeWidth: 3, opacity: 0.4 },
              animated: true,
            };
          }
          return edge;
        })
      );

      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === '4' || node.id === '5') {
            return {
              ...node,
              style: { ...node.style, background: '#fee2e2', border: '2px solid red', animation: 'pulse 2s infinite' },
            };
          }
          return node;
        })
      );
    } else {
      // Simulate "Before PR"
      setEdges(initialEdges);
      setNodes(initialNodes);
    }
  };

  return (
    <div style={{ width: '100%', height: '500px', border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', position: 'relative' }}>
      <button 
        onClick={toggleTimeTravel}
        style={{ position: 'absolute', top: 10, right: 10, zIndex: 10, padding: '8px 16px', background: '#0f172a', color: 'white', borderRadius: '4px', cursor: 'pointer' }}
      >
        {timeTravel ? "⏪ Show Before PR" : "⏩ Show After PR (Time Travel)"}
      </button>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
