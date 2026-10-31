import React, { useMemo, useState } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Node,
  Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CaseGraph } from '../types';
import { FileText, User, Building, MapPin, Package, Clock, Activity, Info } from 'lucide-react';

interface CaseGraphViewerProps {
  graph: CaseGraph;
}

export const CaseGraphViewer: React.FC<CaseGraphViewerProps> = ({ graph }) => {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [filterType, setFilterType] = useState<string>('all');

  // Convert graph data into React Flow nodes and edges with layout
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    const nodePositions: Record<string, { x: number; y: number }> = {};
    const cols = 5;
    const spacingX = 260;
    const spacingY = 140;

    graph.nodes.forEach((n, idx) => {
      const row = Math.floor(idx / cols);
      const col = idx % cols;
      const x = col * spacingX + 40;
      const y = row * spacingY + 40;
      nodePositions[n.id] = { x, y };

      let bgColor = '#FFFFFF';
      let borderColor = '#C9962F';
      let iconColor = '#131A2E';

      if (n.node_type === 'document') {
        bgColor = '#EEF2FF';
        borderColor = '#4F46E5';
      } else if (n.node_type === 'event') {
        bgColor = '#FEF2F2';
        borderColor = '#DC2626';
      } else if (n.node_type === 'time') {
        bgColor = '#F0FDFA';
        borderColor = '#0D9488';
      } else if (n.node_type === 'entity') {
        if (n.sub_type === 'person') {
          bgColor = '#FFFBEB';
          borderColor = '#D97706';
        } else if (n.sub_type === 'organization') {
          bgColor = '#FAF5FF';
          borderColor = '#9333EA';
        } else if (n.sub_type === 'location') {
          bgColor = '#F0FDF4';
          borderColor = '#16A34A';
        } else {
          bgColor = '#FFF7ED';
          borderColor = '#EA580C';
        }
      }

      nodes.push({
        id: n.id,
        position: { x, y },
        data: {
          label: (
            <div className="p-2 text-left">
              <div className="flex items-center space-x-1.5 text-[10px] uppercase font-bold tracking-wider text-gray-500 mb-0.5">
                {n.node_type === 'document' && <FileText className="w-3 h-3 text-indigo-600" />}
                {n.node_type === 'event' && <Activity className="w-3 h-3 text-red-600" />}
                {n.node_type === 'time' && <Clock className="w-3 h-3 text-teal-600" />}
                {n.node_type === 'entity' && n.sub_type === 'person' && <User className="w-3 h-3 text-amber-600" />}
                {n.node_type === 'entity' && n.sub_type === 'organization' && <Building className="w-3 h-3 text-purple-600" />}
                {n.node_type === 'entity' && n.sub_type === 'location' && <MapPin className="w-3 h-3 text-green-600" />}
                {n.node_type === 'entity' && n.sub_type === 'object' && <Package className="w-3 h-3 text-orange-600" />}
                <span>{n.sub_type || n.node_type}</span>
              </div>
              <div className="text-xs font-semibold text-[#131A2E] truncate max-w-[180px]">
                {n.label}
              </div>
            </div>
          ),
          raw: n,
        },
        style: {
          backgroundColor: bgColor,
          borderColor: borderColor,
          borderWidth: '1.5px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          width: 200,
        },
      });
    });

    graph.edges.forEach((e) => {
      edges.push({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.relation.replace(/_/g, ' '),
        animated: e.relation === 'before' || e.relation === 'provides_evidence',
        style: { stroke: '#7A8AA8', strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#7A8AA8',
          width: 14,
          height: 14,
        },
        labelStyle: { fill: '#131A2E', fontSize: 10, fontWeight: 500 },
        labelBgStyle: { fill: '#FAF7EF', fillOpacity: 0.9 },
      });
    });

    return { initialNodes: nodes, initialEdges: edges };
  }, [graph]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  // Filter nodes if user chooses
  const filteredNodes = useMemo(() => {
    if (filterType === 'all') return nodes;
    return nodes.filter((n) => {
      const raw = (n.data as any)?.raw;
      if (!raw) return true;
      if (filterType === 'entity') return raw.node_type === 'entity';
      if (filterType === 'event') return raw.node_type === 'event';
      if (filterType === 'document') return raw.node_type === 'document';
      if (filterType === 'time') return raw.node_type === 'time';
      return true;
    });
  }, [nodes, filterType]);

  return (
    <div className="relative w-full h-[650px] bg-[#FAF8F3] border border-[#E2DDD0] rounded-lg overflow-hidden shadow-inner">
      {/* Top Filter Bar */}
      <div className="absolute top-3 left-3 z-10 bg-white/90 backdrop-blur-sm px-3 py-1.5 rounded-md border border-[#E2DDD0] shadow flex items-center space-x-2 text-xs">
        <span className="font-semibold text-gray-700">Filter Nodes:</span>
        {['all', 'entity', 'event', 'document', 'time'].map((type) => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-2 py-0.5 rounded capitalize transition ${
              filterType === type
                ? 'bg-[#131A2E] text-white font-bold'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      <ReactFlow
        nodes={filteredNodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => setSelectedNode(node.data?.raw)}
        fitView
      >
        <Controls />
        <MiniMap
          nodeColor={(n: any) => {
            if (n.data?.raw?.node_type === 'document') return '#4F46E5';
            if (n.data?.raw?.node_type === 'event') return '#DC2626';
            if (n.data?.raw?.node_type === 'time') return '#0D9488';
            return '#D97706';
          }}
          style={{ backgroundColor: '#FAF7EF' }}
        />
        <Background color="#D4CEBF" gap={16} />
      </ReactFlow>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="absolute bottom-4 right-4 z-20 w-80 bg-white p-4 rounded-lg border border-[#C9962F] shadow-xl">
          <div className="flex items-center justify-between border-b pb-2 mb-2">
            <div className="text-xs font-bold uppercase tracking-wide text-[#C9962F]">
              {selectedNode.sub_type || selectedNode.node_type} Details
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-gray-600 text-sm font-bold"
            >
              ✕
            </button>
          </div>
          <h4 className="text-sm font-bold text-[#131A2E]">{selectedNode.label}</h4>
          <div className="mt-2 text-xs space-y-1 text-gray-600">
            <p><strong>Node ID:</strong> <code className="text-[11px] bg-gray-100 px-1">{selectedNode.id}</code></p>
            {selectedNode.properties && Object.entries(selectedNode.properties).map(([k, v]) => (
              <p key={k} className="truncate">
                <strong className="capitalize">{k}:</strong> {String(v)}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
