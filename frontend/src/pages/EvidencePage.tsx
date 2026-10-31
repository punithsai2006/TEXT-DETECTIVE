import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { EvidenceItem } from '../types';
import { EvidenceCard } from '../components/EvidenceCard';
import { Search, Sliders, Sparkles, AlertCircle } from 'lucide-react';

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
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
          RAG Hybrid Retrieval Engine
        </div>
        <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
          Semantic Evidence Search
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Query persistent ChromaDB vector store and BM25 lexical index with Reciprocal Rank Fusion (RRF).
        </p>
      </div>

      {/* Search Bar Card */}
      <div className="case-card p-4 rounded-lg space-y-3">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Ask an investigative claim or semantic question..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs border border-gray-300 rounded-lg focus:border-[#C9962F] focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-5 py-2 bg-[#131A2E] text-white text-xs font-bold rounded-lg hover:bg-[#1D2744] transition disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Retrieve Evidence'}
          </button>
        </form>

        {/* Quick Query Pills */}
        <div className="flex items-center space-x-1.5 flex-wrap gap-1 text-[11px] text-gray-500">
          <span className="font-semibold text-gray-700 flex items-center">
            <Sparkles className="w-3 h-3 text-[#C9962F] mr-1" /> Try:
          </span>
          {sampleQueries.map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setQuery(sq);
              }}
              className="px-2 py-0.5 rounded bg-gray-100 hover:bg-[#F4F0E6] text-gray-700 transition"
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Slider Controls */}
        <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-2">
            <Sliders className="w-3.5 h-3.5 text-[#C9962F]" />
            <span>Top-K Passages: <strong>{topK}</strong></span>
          </div>
          <input
            type="range"
            min={3}
            max={20}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-36 accent-[#C9962F]"
          />
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-700 font-mono">
            {hasSearched ? `Retrieval Results (${evidenceList.length})` : `Baseline Key Evidence (${evidenceList.length})`}
          </h3>
          <span className="text-[11px] text-gray-400">
            Ranked by Reciprocal Rank Fusion & Cosine Score
          </span>
        </div>

        {evidenceList.length === 0 ? (
          <div className="case-card p-10 text-center rounded-lg text-gray-500 text-xs">
            <AlertCircle className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p>No matching evidence items found for this query in <strong>{activeCase?.name}</strong>.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {evidenceList.map((item, idx) => (
              <EvidenceCard key={item.evidence_id || idx} evidence={item} rank={idx + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
