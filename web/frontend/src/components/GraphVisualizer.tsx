import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
} from 'reactflow';
import 'reactflow/dist/style.css';

export default function GraphVisualizer({ nodes = [], edges = [] }: { nodes?: any[], edges?: any[] }) {
  return (
    <div style={{ width: '100%', height: '500px', border: '1px solid #1e293b', borderRadius: '8px', overflow: 'hidden', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        minZoom={0.2}
      >
        <Controls />
        <MiniMap
          maskColor="rgba(15,23,42,0.7)"
          nodeColor={(n: any) => (n?.data?.isLeakNode ? '#ef4444' : '#334155')}
          style={{ background: '#0f172a', border: '1px solid #1e293b' }}
        />
        <Background variant="dots" gap={12} size={1} color="#1e293b" />
      </ReactFlow>
    </div>
  );
}
