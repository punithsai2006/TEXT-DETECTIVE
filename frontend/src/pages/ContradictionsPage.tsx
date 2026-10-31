import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { ContradictionItem } from '../types';
import { ContradictionCard } from '../components/ContradictionCard';
import { Scale, AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';

export const ContradictionsPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [contradictions, setContradictions] = useState<ContradictionItem[]>([]);
  const [filter, setFilter] = useState<'all' | 'confirmed' | 'possible' | 'agreement'>('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeCaseId) return;
    setLoading(true);
    api
      .getContradictions(activeCaseId)
      .then((items) => setContradictions(items))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [activeCaseId]);

  const confirmedCount = contradictions.filter((c) => c.contradiction_type === 'confirmed_contradiction').length;
  const possibleCount = contradictions.filter((c) => c.contradiction_type === 'possible_contradiction').length;
  const agreementCount = contradictions.filter((c) => c.contradiction_type === 'agreement').length;

  const filtered = contradictions.filter((c) => {
    if (filter === 'confirmed') return c.contradiction_type === 'confirmed_contradiction';
    if (filter === 'possible') return c.contradiction_type === 'possible_contradiction';
    if (filter === 'agreement') return c.contradiction_type === 'agreement';
    return true;
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
          Cross-Document Linking Agent
        </div>
        <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
          Contradictions & Factual Conflicts
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          RoBERTa-MNLI and agentic inference comparing claims across heterogeneous files in <strong>{activeCase?.name}</strong>.
        </p>
      </div>

      {/* Summary KPI Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="case-card p-3 rounded-lg border-l-4 border-l-red-600 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-red-800">Confirmed Conflicts</div>
            <div className="text-xl font-bold font-mono text-red-600 mt-0.5">{confirmedCount}</div>
          </div>
          <AlertTriangle className="w-6 h-6 text-red-400" />
        </div>

        <div className="case-card p-3 rounded-lg border-l-4 border-l-amber-500 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-amber-800">Possible Conflicts</div>
            <div className="text-xl font-bold font-mono text-amber-600 mt-0.5">{possibleCount}</div>
          </div>
          <Scale className="w-6 h-6 text-amber-400" />
        </div>

        <div className="case-card p-3 rounded-lg border-l-4 border-l-emerald-600 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-emerald-800">Corroborated Agreements</div>
            <div className="text-xl font-bold font-mono text-emerald-600 mt-0.5">{agreementCount}</div>
          </div>
          <CheckCircle className="w-6 h-6 text-emerald-400" />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 text-xs">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1.5 rounded-md font-medium transition ${
            filter === 'all'
              ? 'bg-[#131A2E] text-white font-bold'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          All Items ({contradictions.length})
        </button>
        <button
          onClick={() => setFilter('confirmed')}
          className={`px-3 py-1.5 rounded-md font-medium transition ${
            filter === 'confirmed'
              ? 'bg-red-700 text-white font-bold'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          Confirmed Conflicts ({confirmedCount})
        </button>
        <button
          onClick={() => setFilter('possible')}
          className={`px-3 py-1.5 rounded-md font-medium transition ${
            filter === 'possible'
              ? 'bg-amber-600 text-white font-bold'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          Possible Conflicts ({possibleCount})
        </button>
        <button
          onClick={() => setFilter('agreement')}
          className={`px-3 py-1.5 rounded-md font-medium transition ${
            filter === 'agreement'
              ? 'bg-emerald-700 text-white font-bold'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          Corroborated Agreements ({agreementCount})
        </button>
      </div>

      {/* Contradiction Cards */}
      {filtered.length === 0 ? (
        <div className="case-card p-12 text-center rounded-lg text-gray-500 text-xs">
          <Scale className="w-10 h-10 text-gray-300 mx-auto mb-2" />
          <p>No contradictions or discrepancies found matching the selected filter.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((item, idx) => (
            <ContradictionCard key={item.id || idx} item={item} index={idx + 1} />
          ))}
        </div>
      )}
    </div>
  );
};
