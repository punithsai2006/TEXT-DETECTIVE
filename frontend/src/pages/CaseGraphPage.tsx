import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { CaseGraph } from '../types';
import { CaseGraphViewer } from '../components/CaseGraphViewer';
import { Network, Info, RefreshCw, Table, Share2 } from 'lucide-react';

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
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
            Relational Knowledge Topology
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
            Knowledge Graph Visualization
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Interactive node-link topology linking Entities, Events, Documents, and Timestamps for <strong>{activeCase?.name}</strong>.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono text-slate-500">
          <span>Nodes: <strong className="text-slate-800">{graph.nodes.length}</strong></span>
          <span>•</span>
          <span>Edges: <strong className="text-slate-800">{graph.edges.length}</strong></span>

          <div className="flex items-center rounded-lg border border-slate-300 overflow-hidden bg-white shadow-sm ml-2 p-0.5">
            <button
              onClick={() => setViewMode('graph')}
              className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-semibold rounded-md transition ${
                viewMode === 'graph' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Share2 className="w-3.5 h-3.5" />
              <span>Canvas</span>
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-semibold rounded-md transition ${
                viewMode === 'table' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Table className="w-3.5 h-3.5" />
              <span>Topology</span>
            </button>
          </div>
        </div>
      </div>

      {/* Legend & Instructions */}
      <div className="case-card p-4 rounded-xl flex items-center justify-between flex-wrap gap-3 text-xs shadow-sm border border-slate-200/80">
        <div className="flex items-center space-x-4 flex-wrap gap-2 text-slate-700">
          <span className="font-bold text-slate-900">Node Types:</span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span><span className="font-medium">Person</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block"></span><span className="font-medium">Organization</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span><span className="font-medium">Location</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-orange-500 inline-block"></span><span className="font-medium">Object</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-600 inline-block"></span><span className="font-medium">Event (Action)</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-indigo-600 inline-block"></span><span className="font-medium">Document</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-teal-600 inline-block"></span><span className="font-medium">Time</span></span>
        </div>

        <div className="text-[11px] text-slate-400 italic">
          Click any node to inspect properties and source sentences.
        </div>
      </div>

      {/* Content View */}
      {graph.nodes.length === 0 ? (
        <div className="case-card p-16 text-center rounded-2xl text-slate-400 text-xs">
          <Network className="w-12 h-12 mx-auto text-slate-300 mb-2" />
          <p>No graph nodes extracted yet. Run the investigation pipeline to generate the knowledge graph.</p>
        </div>
      ) : viewMode === 'table' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Nodes Table */}
          <div className="case-card p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-600 border-b border-slate-100 pb-2">
              Entities & Knowledge Nodes ({graph.nodes.length})
            </h3>
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 text-slate-600 font-mono text-[10px] uppercase">
                  <tr>
                    <th className="p-2.5 border-b border-slate-200">Node Label</th>
                    <th className="p-2.5 border-b border-slate-200">Type</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {graph.nodes.map((n) => (
                    <tr key={n.id} className="hover:bg-slate-50">
                      <td className="p-2.5 font-medium text-slate-800">{n.label}</td>
                      <td className="p-2.5 font-mono text-[10px] uppercase text-slate-500">{n.node_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Edges Table */}
          <div className="case-card p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-600 border-b border-slate-100 pb-2">
              Extracted Relational Edges ({graph.edges.length})
            </h3>
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 text-slate-600 font-mono text-[10px] uppercase">
                  <tr>
                    <th className="p-2.5 border-b border-slate-200">Source</th>
                    <th className="p-2.5 border-b border-slate-200">Relation</th>
                    <th className="p-2.5 border-b border-slate-200">Target</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {graph.edges.map((e) => (
                    <tr key={e.id} className="hover:bg-slate-50">
                      <td className="p-2.5 text-slate-800 text-[11px] truncate max-w-[120px]">{e.source}</td>
                      <td className="p-2.5 font-mono text-[10px] font-bold text-blue-600 whitespace-nowrap">{e.relation}</td>
                      <td className="p-2.5 text-slate-800 text-[11px] truncate max-w-[120px]">{e.target}</td>
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
