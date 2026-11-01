import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { EvidenceItem } from '../types';
import { EvidenceCard } from '../components/EvidenceCard';
import { Search, Sliders, Sparkles, AlertCircle, Database, Layers } from 'lucide-react';

export const EvidencePage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    if (!activeCaseId) return;
    // Load initial baseline key evidence
    api
      .getKeyEvidence(activeCaseId)
      .then((items) => setEvidenceList(items))
      .catch((e) => console.error(e));
  }, [activeCaseId]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCaseId || !query.trim()) return;
    setLoading(true);
    setHasSearched(true);
    try {
      const results = await api.searchEvidence(activeCaseId, query.trim(), topK);
      setEvidenceList(results);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    'Who entered Server Room B and at what time?',
    'What physical USB or mass storage device was plugged in?',
    'Where was the master keycard seen in the breakroom?',
    'What time did the contractor exit the facility?',
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
          Hybrid Vector & Keyword Search
        </div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
          Semantic Evidence Search
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          Query persistent ChromaDB vector store and BM25 lexical index using Reciprocal Rank Fusion (RRF).
        </p>
      </div>

      {/* Search Bar Card */}
      <div className="case-card p-5 sm:p-6 rounded-2xl space-y-4 shadow-sm border border-slate-200/80">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2.5">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              placeholder="Query investigative claims, timestamps, locations, or suspect actions..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm border border-slate-300 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none shadow-sm"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-xs font-semibold rounded-xl transition disabled:opacity-50 shadow-sm shrink-0 flex items-center justify-center gap-1.5"
          >
            <Search className="w-3.5 h-3.5" />
            <span>{loading ? 'Searching...' : 'Retrieve Evidence'}</span>
          </button>
        </form>

        {/* Quick Query Pills */}
        <div className="flex items-center space-x-1.5 flex-wrap gap-1.5 text-[11px] text-slate-500 pt-1">
          <span className="font-semibold text-slate-700 flex items-center mr-1">
            <Sparkles className="w-3.5 h-3.5 text-blue-600 mr-1" /> Try queries:
          </span>
          {sampleQueries.map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setQuery(sq);
              }}
              className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 transition border border-slate-200/60"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between px-1 text-xs font-bold uppercase tracking-wider text-slate-500">
        <span>{hasSearched ? 'Search Results' : 'Key Baseline Evidence'} ({evidenceList.length})</span>
        <span className="text-[10px] font-mono text-slate-400">Hybrid Dense + Lexical RRF</span>
      </div>

      {/* Evidence Items List */}
      {loading ? (
        <div className="case-card p-12 text-center text-xs text-slate-500 font-mono rounded-2xl">
          Executing hybrid dense-lexical vector search...
        </div>
      ) : evidenceList.length === 0 ? (
        <div className="case-card p-12 text-center rounded-2xl">
          <Database className="w-10 h-10 text-slate-300 mx-auto mb-2" />
          <h4 className="text-base font-bold text-slate-800">No Evidence Found</h4>
          <p className="text-xs text-slate-500 mt-1">
            Try a different search query or check that documents have been ingested and analyzed.
          </p>
        </div>
      ) : (
        <div className="space-y-3.5">
          {evidenceList.map((item, idx) => (
            <EvidenceCard key={item.evidence_id || idx} evidence={item} rank={idx + 1} />
          ))}
        </div>
      )}
    </div>
  );
};
