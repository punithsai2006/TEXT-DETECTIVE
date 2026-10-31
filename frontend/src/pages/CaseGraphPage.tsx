import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { CaseGraph } from '../types';
import { CaseGraphViewer } from '../components/CaseGraphViewer';
import { Network, Info, RefreshCw } from 'lucide-react';

export const CaseGraphPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [graph, setGraph] = useState<CaseGraph>({ nodes: [], edges: [] });
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

      {/* React Flow Interactive Graph */}
      {graph.nodes.length === 0 ? (
        <div className="case-card p-16 text-center rounded-lg text-gray-400 text-xs">
          <Network className="w-12 h-12 mx-auto text-gray-300 mb-2" />
          <p>No graph nodes extracted yet. Run the investigation pipeline to generate the knowledge graph.</p>
        </div>
      ) : (
        <CaseGraphViewer graph={graph} />
      )}
    </div>
  );
};
