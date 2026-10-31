import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { ContradictionItem, ReviewStatus } from '../types';
import { ContradictionCard } from '../components/ContradictionCard';
import { Scale, AlertTriangle, CheckCircle, ShieldAlert, Filter } from 'lucide-react';

export const ContradictionsPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [contradictions, setContradictions] = useState<ContradictionItem[]>([]);
  const [filter, setFilter] = useState<'all' | 'confirmed' | 'possible' | 'agreement'>('all');
  const [reviewFilter, setReviewFilter] = useState<'all' | ReviewStatus>('all');
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

  const handleReviewUpdate = async (id: string, newStatus: ReviewStatus, notes?: string) => {
    if (!activeCaseId) return;
    try {
      const updated = await api.reviewContradiction(activeCaseId, id, newStatus, 'forensic_analyst', notes);
      setContradictions((prev) => prev.map((item) => (item.id === id ? updated : item)));
    } catch (err) {
      console.error('Failed to update review status:', err);
    }
  };

  const confirmedCount = contradictions.filter((c) => c.contradiction_type === 'confirmed_contradiction').length;
  const possibleCount = contradictions.filter((c) => c.contradiction_type === 'possible_contradiction').length;
  const agreementCount = contradictions.filter((c) => c.contradiction_type === 'agreement').length;

  const filtered = contradictions.filter((c) => {
    // Type filter
    if (filter === 'confirmed' && c.contradiction_type !== 'confirmed_contradiction') return false;
    if (filter === 'possible' && c.contradiction_type !== 'possible_contradiction') return false;
    if (filter === 'agreement' && c.contradiction_type !== 'agreement') return false;

    // Review status filter
    if (reviewFilter !== 'all') {
      const itemStatus = c.review_status || 'pending_review';
      if (itemStatus !== reviewFilter) return false;
    }

    return true;
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
          Cross-Document Linking Agent (Module 4)
        </div>
        <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
          Contradictions & Factual Conflicts
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          RoBERTa-MNLI and rule engine comparing claims across files in <strong>{activeCase?.name}</strong>.
          Confidence values represent heuristic discrepancy severity, not probability.
        </p>
      </div>

      {/* Summary KPI Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="case-card p-3 rounded-lg border-l-4 border-l-red-600 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-red-800">Confirmed Conflicts</div>
            <div className="text-xl font-bold font-mono text-red-600 mt-0.5">{confirmedCount}</div>
          </div>
          <AlertTriangle className="w-6 h-6 text-red-400" aria-hidden="true" />
        </div>

        <div className="case-card p-3 rounded-lg border-l-4 border-l-amber-500 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-amber-800">Possible Conflicts</div>
            <div className="text-xl font-bold font-mono text-amber-600 mt-0.5">{possibleCount}</div>
          </div>
          <Scale className="w-6 h-6 text-amber-400" aria-hidden="true" />
        </div>

        <div className="case-card p-3 rounded-lg border-l-4 border-l-emerald-600 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-emerald-800">Corroborated Agreements</div>
            <div className="text-xl font-bold font-mono text-emerald-600 mt-0.5">{agreementCount}</div>
          </div>
          <CheckCircle className="w-6 h-6 text-emerald-400" aria-hidden="true" />
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-3 rounded-lg border border-gray-200 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          {/* Conflict Type Tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="font-semibold text-gray-600 text-[11px] mr-1 flex items-center">
              <Filter className="w-3 h-3 mr-1 text-[#C9962F]" /> Discrepancy Type:
            </span>
            <button
              onClick={() => setFilter('all')}
              className={`px-2.5 py-1 rounded text-xs transition ${
                filter === 'all'
                  ? 'bg-[#131A2E] text-white font-bold'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              All ({contradictions.length})
            </button>
            <button
              onClick={() => setFilter('confirmed')}
              className={`px-2.5 py-1 rounded text-xs transition ${
                filter === 'confirmed'
                  ? 'bg-red-700 text-white font-bold'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Confirmed ({confirmedCount})
            </button>
            <button
              onClick={() => setFilter('possible')}
              className={`px-2.5 py-1 rounded text-xs transition ${
                filter === 'possible'
                  ? 'bg-amber-600 text-white font-bold'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Possible ({possibleCount})
            </button>
            <button
              onClick={() => setFilter('agreement')}
              className={`px-2.5 py-1 rounded text-xs transition ${
                filter === 'agreement'
                  ? 'bg-emerald-700 text-white font-bold'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Agreements ({agreementCount})
            </button>
          </div>

          {/* Review Status Filter */}
          <div className="flex items-center gap-1.5 text-[11px]">
            <span className="text-gray-500 font-medium">Review Status:</span>
            <select
              value={reviewFilter}
              onChange={(e) => setReviewFilter(e.target.value as any)}
              className="px-2 py-1 bg-gray-50 border border-gray-300 rounded text-xs font-mono text-[#131A2E]"
              aria-label="Filter contradictions by human review status"
            >
              <option value="all">All Statuses</option>
              <option value="pending_review">Pending Review</option>
              <option value="confirmed">Confirmed</option>
              <option value="rejected">Rejected</option>
              <option value="needs_further_investigation">Needs Investigation</option>
            </select>
          </div>
        </div>
      </div>

      {/* Contradictions List */}
      {loading ? (
        <div className="case-card p-8 text-center text-xs text-gray-500 font-mono">
          Evaluating cross-document statement pairs...
        </div>
      ) : filtered.length === 0 ? (
        <div className="case-card p-8 text-center rounded-lg">
          <ShieldAlert className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <div className="font-bold text-sm text-[#131A2E]">No matching items</div>
          <p className="text-xs text-gray-500 mt-1">
            No contradictions match the selected filter criteria.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((item, idx) => (
            <ContradictionCard
              key={item.id}
              item={item}
              index={idx + 1}
              onUpdateReview={handleReviewUpdate}
            />
          ))}
        </div>
      )}
    </div>
  );
};
