import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
} from 'reactflow';
import 'reactflow/dist/style.css';

export default function GraphVisualizer({ nodes = [], edges = [] }: { nodes?: any[], edges?: any[] }) {
  return (
    <div style={{ width: '100%', height: '500px', border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
