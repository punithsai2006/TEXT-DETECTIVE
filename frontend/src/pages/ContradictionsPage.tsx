import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { ContradictionItem, ReviewStatus } from '../types';
import { ContradictionCard } from '../components/ContradictionCard';
import { Scale, AlertTriangle, CheckCircle, ShieldAlert, Filter, AlertOctagon } from 'lucide-react';

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
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
          Module 4 • Cross-Document Linking & NLI Engine
        </div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
          Contradictions & Factual Conflicts
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          RoBERTa-MNLI and rule engine evaluating pairwise claims across files in <strong>{activeCase?.name}</strong>.
          Confidence scores indicate heuristic discrepancy severity.
        </p>
      </div>

      {/* Summary KPI Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <div className="case-card p-4 rounded-xl border-l-4 border-l-rose-600 flex items-center justify-between shadow-sm">
          <div>
            <div className="text-[10px] uppercase font-bold text-rose-700 tracking-wider">Confirmed Conflicts</div>
            <div className="text-2xl font-bold font-mono text-rose-600 mt-0.5">{confirmedCount}</div>
          </div>
          <div className="p-2 rounded-lg bg-rose-50 text-rose-600">
            <AlertOctagon className="w-6 h-6" aria-hidden="true" />
          </div>
        </div>

        <div className="case-card p-4 rounded-xl border-l-4 border-l-amber-500 flex items-center justify-between shadow-sm">
          <div>
            <div className="text-[10px] uppercase font-bold text-amber-700 tracking-wider">Possible Conflicts</div>
            <div className="text-2xl font-bold font-mono text-amber-600 mt-0.5">{possibleCount}</div>
          </div>
          <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
            <Scale className="w-6 h-6" aria-hidden="true" />
          </div>
        </div>

        <div className="case-card p-4 rounded-xl border-l-4 border-l-emerald-600 flex items-center justify-between shadow-sm">
          <div>
            <div className="text-[10px] uppercase font-bold text-emerald-700 tracking-wider">Corroborated Agreements</div>
            <div className="text-2xl font-bold font-mono text-emerald-600 mt-0.5">{agreementCount}</div>
          </div>
          <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
            <CheckCircle className="w-6 h-6" aria-hidden="true" />
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="case-card p-3.5 rounded-xl border border-slate-200/80 shadow-sm space-y-2.5">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Conflict Type Tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="font-semibold text-slate-500 text-[11px] mr-1 flex items-center">
              <Filter className="w-3.5 h-3.5 mr-1 text-blue-600" /> Discrepancy Type:
            </span>
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                filter === 'all'
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              All ({contradictions.length})
            </button>
            <button
              onClick={() => setFilter('confirmed')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                filter === 'confirmed'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Confirmed ({confirmedCount})
            </button>
            <button
              onClick={() => setFilter('possible')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                filter === 'possible'
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Possible ({possibleCount})
            </button>
            <button
              onClick={() => setFilter('agreement')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                filter === 'agreement'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Agreements ({agreementCount})
            </button>
          </div>

          {/* Review Status Filter */}
          <div className="flex items-center gap-2 text-[11px]">
            <span className="text-slate-500 font-medium">Review Status:</span>
            <select
              value={reviewFilter}
              onChange={(e) => setReviewFilter(e.target.value as any)}
              className="px-2.5 py-1 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm cursor-pointer"
              aria-label="Filter contradictions by human review status"
            >
              <option value="all">All Review Statuses</option>
              <option value="pending_review">Pending Review</option>
              <option value="confirmed">Confirmed Valid</option>
              <option value="rejected">Rejected / Dismissed</option>
              <option value="needs_further_investigation">Needs Investigation</option>
            </select>
          </div>
        </div>
      </div>

      {/* Contradictions List */}
      {loading ? (
        <div className="case-card p-12 text-center text-xs text-slate-500 font-mono rounded-xl">
          Evaluating cross-document statement pairs...
        </div>
      ) : filtered.length === 0 ? (
        <div className="case-card p-12 text-center rounded-2xl">
          <ShieldAlert className="w-10 h-10 text-slate-300 mx-auto mb-2" />
          <div className="font-bold text-sm text-slate-800">No matching items</div>
          <p className="text-xs text-slate-500 mt-1">
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
