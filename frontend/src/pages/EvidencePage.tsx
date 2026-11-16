import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { EvidenceItem, DocumentMetadata } from '../types';
import { EvidenceCard } from '../components/EvidenceCard';
import { Search, Sliders, Sparkles, AlertCircle, Database, Layers } from 'lucide-react';

export const EvidencePage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [documentId, setDocumentId] = useState('');
  const [mode, setMode] = useState('hybrid');
  const [entity, setEntity] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [evidenceType, setEvidenceType] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!activeCaseId) return;
    setEvidenceList([]); setDocumentId(''); setHasSearched(false);
    api.getCaseDocuments(activeCaseId).then(setDocuments).catch(e => setError(e.message));
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
    setError('');
    setHasSearched(true);
    try {
      const results = await api.searchEvidence(activeCaseId, query.trim(), topK, 0, {
        mode, ...(documentId ? { document_ids: [documentId] } : {}), entity: entity || undefined,
        date_from: dateFrom || undefined, date_to: dateTo || undefined, evidence_type: evidenceType || undefined,
      });
      setEvidenceList(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed; existing results are retained.');
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    'Which passages describe access to the location?',
    'What objects or credentials are mentioned?',
    'Which accounts describe different event times?',
    'What context is available for a reported event?',
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
          Inspect original case passages. Semantic retrieval is used when a local embedding model is available; lexical retrieval remains available without an LLM.
        </p>
      </div>

      {/* Search Bar Card */}
      <div className="case-card p-5 sm:p-6 rounded-2xl space-y-4 shadow-sm border border-slate-200/80">
        {error && <p role="alert" className="text-red-700 text-sm">{error}</p>}
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

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
          <label>Search mode<select aria-label="Search mode" className="block w-full border rounded p-2" value={mode} onChange={e => setMode(e.target.value)}><option value="hybrid">Natural-language retrieval</option><option value="exact">Exact phrase (case-insensitive)</option></select></label>
          <label>Document<select className="block w-full border rounded p-2" value={documentId} onChange={e => setDocumentId(e.target.value)}><option value="">All documents</option>{documents.map(d => <option key={d.document_id} value={d.document_id}>{d.filename}</option>)}</select></label>
          <label>Entity / location<input className="block w-full border rounded p-2" value={entity} onChange={e => setEntity(e.target.value)} placeholder="Exact extracted name" /></label>
          <label>Event date from<input type="date" className="block w-full border rounded p-2" value={dateFrom} onChange={e => setDateFrom(e.target.value)} /></label>
          <label>Event date to<input type="date" className="block w-full border rounded p-2" value={dateTo} onChange={e => setDateTo(e.target.value)} /></label>
          <label>Evidence type<select className="block w-full border rounded p-2" value={evidenceType} onChange={e => setEvidenceType(e.target.value)}><option value="">All types</option>{['interview', 'email', 'report', 'log', 'other'].map(t => <option key={t}>{t}</option>)}</select></label>
          <label>Maximum results<input type="number" min={1} max={50} className="block w-full border rounded p-2" value={topK} onChange={e => setTopK(Math.max(1, Math.min(50, Number(e.target.value))))} /></label>
        </div>
        <p className="text-xs text-slate-500">Date/entity filters use current extracted claims. Unknown event dates are excluded when filtering; document dates are not substituted.</p>
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
        <span className="text-[10px] font-mono text-slate-400">Original passages remain visible independently of synthesis</span>
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
