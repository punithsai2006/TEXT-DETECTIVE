import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { CaseGraph } from '../types';
import { CaseGraphViewer } from '../components/CaseGraphViewer';
import { Network, Info, RefreshCw } from 'lucide-react';

export const CaseGraphPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [graph, setGraph] = useState<CaseGraph>({ nodes: [], edges: [] });
  const [viewMode, setViewMode] = useState<'graph' | 'table'>('graph');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeCaseId) return;
    setLoading(true);
    api
      .getCaseGraph(activeCaseId)
      .then((g) => setGraph(g))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [activeCaseId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-gray-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
            Slide 16 Case Graph Specification
          </div>
          <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
            Structured Investigation Knowledge Graph
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Interactive node-link visualization mapping Entities, Events, Documents, and Timestamps for <strong>{activeCase?.name}</strong>.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono text-gray-500">
          <span>Nodes: <strong>{graph.nodes.length}</strong></span>
          <span>•</span>
          <span>Edges: <strong>{graph.edges.length}</strong></span>

          <div className="flex items-center rounded border border-gray-300 overflow-hidden bg-white ml-2">
            <button
              onClick={() => setViewMode('graph')}
              className={`px-2.5 py-1 text-xs font-semibold ${
                viewMode === 'graph' ? 'bg-[#131A2E] text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Graph Canvas
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-2.5 py-1 text-xs font-semibold ${
                viewMode === 'table' ? 'bg-[#131A2E] text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Topology Table
            </button>
          </div>
        </div>
      </div>

      {/* Legend & Instructions */}
      <div className="case-card p-3 rounded-lg flex items-center justify-between flex-wrap gap-2 text-xs">
        <div className="flex items-center space-x-4 flex-wrap gap-2">
          <span className="font-semibold text-gray-700">Legend:</span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span><span>Person</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block"></span><span>Organization</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block"></span><span>Location</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-orange-500 inline-block"></span><span>Object</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-600 inline-block"></span><span>Event (Action)</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-indigo-600 inline-block"></span><span>Document</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-teal-600 inline-block"></span><span>Time</span></span>
        </div>

        <div className="text-[11px] text-gray-400 italic">
          Click any node to inspect properties and source sentences.
        </div>
      </div>

      {/* Content View */}
      {graph.nodes.length === 0 ? (
        <div className="case-card p-16 text-center rounded-lg text-gray-400 text-xs">
          <Network className="w-12 h-12 mx-auto text-gray-300 mb-2" />
          <p>No graph nodes extracted yet. Run the investigation pipeline to generate the knowledge graph.</p>
        </div>
      ) : viewMode === 'table' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Nodes Table */}
          <div className="case-card p-4 rounded-lg bg-white border border-gray-200 space-y-2">
            <h3 className="font-bold text-xs uppercase font-mono text-[#131A2E] border-b pb-1">
              Entities & Knowledge Nodes ({graph.nodes.length})
            </h3>
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-[#FAF8F3] text-gray-700 font-mono text-[10px] uppercase">
                  <tr>
                    <th className="p-2 border-b">Node Label</th>
                    <th className="p-2 border-b">Type</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-serif">
                  {graph.nodes.map((n) => (
                    <tr key={n.id} className="hover:bg-gray-50">
                      <td className="p-2 font-medium text-[#131A2E]">{n.label}</td>
                      <td className="p-2 font-mono text-[10px] uppercase text-gray-500">{n.node_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Edges Table */}
          <div className="case-card p-4 rounded-lg bg-white border border-gray-200 space-y-2">
            <h3 className="font-bold text-xs uppercase font-mono text-[#131A2E] border-b pb-1">
              Extracted Relational Edges ({graph.edges.length})
            </h3>
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-[#FAF8F3] text-gray-700 font-mono text-[10px] uppercase">
                  <tr>
                    <th className="p-2 border-b">Source</th>
                    <th className="p-2 border-b">Relation</th>
                    <th className="p-2 border-b">Target</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-serif">
                  {graph.edges.map((e) => (
                    <tr key={e.id} className="hover:bg-gray-50">
                      <td className="p-2 text-gray-800 text-[11px] truncate max-w-[120px]">{e.source}</td>
                      <td className="p-2 font-mono text-[10px] font-bold text-[#C9962F] whitespace-nowrap">{e.relation}</td>
                      <td className="p-2 text-gray-800 text-[11px] truncate max-w-[120px]">{e.target}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <CaseGraphViewer graph={graph} />
      )}
    </div>
  );
};
