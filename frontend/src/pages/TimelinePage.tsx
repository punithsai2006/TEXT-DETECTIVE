import React, { useEffect, useState, useMemo } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { ForensicSummaryMilestone, TimelineEntry } from '../types';
import {
  Clock,
  User,
  MapPin,
  FileText,
  AlertCircle,
  Calendar,
  Filter,
  Search,
  Table,
  ListTree,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  GitBranch,
  CheckCircle2,
  XCircle,
  ChevronRight,
} from 'lucide-react';

export const TimelinePage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [summaryTimeline, setSummaryTimeline] = useState<ForensicSummaryMilestone[]>([]);
  const [participantFilter, setParticipantFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [viewMode, setViewMode] = useState<'summary' | 'timeline' | 'table'>('summary');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeCaseId) return;
    setLoading(true);
    Promise.all([
      api.getTimeline(activeCaseId).catch(() => []),
      api.getSummaryTimeline(activeCaseId).catch(() => []),
    ])
      .then(([entries, summary]) => {
        setTimeline(entries);
        setSummaryTimeline(summary);
      })
      .finally(() => setLoading(false));
  }, [activeCaseId]);

  // Extract unique participants across events
  const allParticipants = useMemo(() => {
    const set = new Set<string>();
    timeline.forEach((e) => {
      (e.participants || []).forEach((p) => set.add(p));
    });
    return Array.from(set).sort();
  }, [timeline]);

  const filteredTimeline = useMemo(() => {
    return timeline.filter((entry) => {
      if (participantFilter !== 'all') {
        if (!entry.participants || !entry.participants.includes(participantFilter)) {
          return false;
        }
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchDesc = entry.event_description.toLowerCase().includes(q);
        const matchLoc = (entry.location || '').toLowerCase().includes(q);
        const matchDoc = entry.document_name.toLowerCase().includes(q);
        if (!matchDesc && !matchLoc && !matchDoc) return false;
      }
      return true;
    });
  }, [timeline, participantFilter, searchQuery]);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs uppercase font-bold tracking-wider text-blue-600">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Graph-RAG & Forensic Sequence Intelligence</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
            Forensic Investigation Timeline
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            {viewMode === 'summary' ? (
              <span>
                <strong>{summaryTimeline.length} strategic crime phases</strong> synthesized from the Case Knowledge Graph for case <strong>{activeCase?.name}</strong>.
              </span>
            ) : (
              <span>
                <strong>{timeline.length} sequenced chronological events</strong> extracted across case documents for <strong>{activeCase?.name}</strong>.
              </span>
            )}
          </p>
        </div>

        {/* View Mode & Filter Controls */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs">
          {viewMode !== 'summary' && (
            <>
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search events or locations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 w-44 sm:w-52 shadow-sm"
                  aria-label="Filter timeline events by text"
                />
              </div>

              <select
                value={participantFilter}
                onChange={(e) => setParticipantFilter(e.target.value)}
                className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm cursor-pointer"
                aria-label="Filter timeline events by participant"
              >
                <option value="all">All People ({allParticipants.length})</option>
                {allParticipants.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </>
          )}

          {/* View Mode Toggle: Summary vs Detailed Timeline vs Table */}
          <div className="flex items-center rounded-lg border border-slate-300 overflow-hidden bg-white shadow-sm p-0.5">
            <button
              onClick={() => setViewMode('summary')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition ${
                viewMode === 'summary' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Forensic Summary Timeline synthesized from Case Graph"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Summary (Graph-RAG)</span>
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition ${
                viewMode === 'timeline' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Raw sequenced log events"
            >
              <ListTree className="w-3.5 h-3.5" />
              <span>Sequenced Logs</span>
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition ${
                viewMode === 'table' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Tabular telemetry format"
            >
              <Table className="w-3.5 h-3.5" />
              <span>Table</span>
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="case-card p-12 text-center rounded-2xl">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs text-slate-500">Traversing Case Knowledge Graph & synthesizing timeline milestones...</p>
        </div>
      ) : viewMode === 'summary' ? (
        /* ==============================================================
           FORENSIC SUMMARY TIMELINE (GRAPH-RAG SYNTHESIZED)
           ============================================================== */
        summaryTimeline.length === 0 ? (
          <div className="case-card p-12 text-center rounded-2xl">
            <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-slate-800">No Graph Summary Generated Yet</h3>
            <p className="text-xs text-slate-500 mt-1">
              Run the investigation analysis pipeline on uploaded documents to construct the Case Graph and extract forensic crime phases.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Informational Methodology Callout */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-blue-900/90 to-indigo-900/90 text-white border border-blue-700/60 shadow-sm flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-blue-300 shrink-0 mt-0.5" />
              <div className="text-xs space-y-1">
                <div className="font-bold text-slate-100 flex items-center gap-2">
                  <span>Graph-RAG Narrative Synthesis</span>
                  <span className="text-[10px] bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full border border-blue-400/30">
                    Dual-Channel Retrieval
                  </span>
                </div>
                <p className="text-slate-200 leading-relaxed">
                  Instead of a flat chronological dump of individual sensor records, the <strong>ForensicTimelineAgent</strong> traversed the Case Knowledge Graph to cluster related events, physical keys, vehicles, and CCTV feeds into <strong>5 structured Crime Phases</strong>.
                </p>
              </div>
            </div>

            {/* Milestones Sequence */}
            <div className="space-y-6">
              {summaryTimeline.map((milestone, idx) => (
                <div
                  key={milestone.milestone_id || idx}
                  className="case-card p-5 sm:p-6 rounded-2xl border border-slate-200/90 shadow-sm space-y-4 hover:border-slate-300 transition-all bg-white"
                >
                  {/* Top Bar: Phase Tag, Status Badge, Timestamp Range */}
                  <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-slate-100">
                    <div className="flex items-center space-x-2">
                      <span className="text-[11px] font-bold px-2.5 py-1 rounded-lg uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200/80">
                        {milestone.phase}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      {milestone.status === 'CORROBORATED_FACT' ? (
                        <span className="flex items-center space-x-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Corroborated Telemetry</span>
                        </span>
                      ) : (
                        <span className="flex items-center space-x-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                          <XCircle className="w-3.5 h-3.5 text-rose-600" />
                          <span>Disproven Alibi / Perjury</span>
                        </span>
                      )}

                      <div className="flex items-center space-x-1 text-xs font-mono font-bold text-slate-800 bg-slate-100 px-3 py-1 rounded-lg border border-slate-200">
                        <Clock className="w-3.5 h-3.5 text-blue-600" />
                        <span>{milestone.timestamp_range}</span>
                      </div>
                    </div>
                  </div>

                  {/* Title & Core Narrative */}
                  <div>
                    <h2 className="text-base sm:text-lg font-bold text-slate-900 leading-snug">
                      {milestone.title}
                    </h2>
                    <p className="text-xs sm:text-sm text-slate-700 mt-2 leading-relaxed bg-slate-50/70 p-3.5 rounded-xl border border-slate-100">
                      {milestone.summary}
                    </p>
                  </div>

                  {/* Knowledge Graph Subgraph Paths */}
                  {milestone.graph_relationships && milestone.graph_relationships.length > 0 && (
                    <div className="pt-1 space-y-2">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                        <GitBranch className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Case Graph Relational Traversal</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {milestone.graph_relationships.map((path, pIdx) => (
                          <div
                            key={pIdx}
                            className="text-xs font-mono bg-slate-900 text-blue-200 px-3 py-1 rounded-lg border border-slate-800 flex items-center space-x-1 shadow-sm"
                          >
                            <span>{path}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Multi-Source Corroboration Chips */}
                  {milestone.corroborating_sources && milestone.corroborating_sources.length > 0 && (
                    <div className="pt-1 space-y-2">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Cross-Referenced Physical Telemetry ({milestone.corroborating_sources.length} Sources)</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {milestone.corroborating_sources.map((src, sIdx) => (
                          <div key={sIdx} className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/70 space-y-1">
                            <div className="flex items-center justify-between text-[10px] font-mono">
                              <span className="font-bold text-slate-800 truncate">{src.document}</span>
                              <span className="text-slate-400 uppercase font-semibold">{src.type}</span>
                            </div>
                            {src.excerpt && (
                              <p className="text-[11px] text-slate-600 italic line-clamp-2">
                                "{src.excerpt}"
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Refuted Suspect Claims (If any) */}
                  {milestone.contradicted_suspect_claims && milestone.contradicted_suspect_claims.length > 0 && (
                    <div className="pt-2 p-3.5 bg-rose-50/90 border border-rose-200 rounded-xl space-y-2">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-rose-800 flex items-center gap-1.5">
                        <ShieldAlert className="w-4 h-4 text-rose-600" />
                        <span>Contradicted Testimonial Statements Disproven by This Milestone</span>
                      </div>
                      <ul className="space-y-1.5 text-xs text-rose-900">
                        {milestone.contradicted_suspect_claims.map((claim, cIdx) => (
                          <li key={cIdx} className="flex items-start gap-1.5 leading-relaxed">
                            <span className="text-rose-500 font-bold shrink-0">•</span>
                            <span>{claim}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )
      ) : viewMode === 'table' ? (
        /* ==============================================================
           DETAILED TABULAR VIEW
           ============================================================== */
        <div className="case-card p-4 rounded-2xl bg-white overflow-x-auto border border-slate-200/80 shadow-sm">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 text-slate-600 font-mono text-[10px] uppercase border-b border-slate-200">
              <tr>
                <th className="p-3">#</th>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Event Description</th>
                <th className="p-3">Participants</th>
                <th className="p-3">Location</th>
                <th className="p-3">Source Document</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredTimeline.map((entry, idx) => (
                <tr key={entry.entry_id || idx} className="hover:bg-slate-50 transition-colors">
                  <td className="p-3 font-mono text-[10px] text-slate-400">{idx + 1}</td>
                  <td className="p-3 font-mono font-bold text-slate-900 whitespace-nowrap">
                    {entry.timestamp_display}
                    {entry.is_uncertain && (
                      <span className="ml-1.5 text-[9px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded-full font-sans border border-amber-200">
                        approx
                      </span>
                    )}
                  </td>
                  <td className="p-3 text-slate-800 max-w-sm leading-relaxed">{entry.event_description}</td>
                  <td className="p-3 text-blue-700 whitespace-nowrap font-medium">
                    {entry.participants && entry.participants.length > 0 ? entry.participants.join(', ') : '—'}
                  </td>
                  <td className="p-3 text-emerald-700 whitespace-nowrap font-medium">
                    {entry.location || '—'}
                  </td>
                  <td className="p-3 font-mono text-[10px] text-slate-500 whitespace-nowrap">
                    {entry.document_name}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        /* ==============================================================
           SEQUENCED LOGS TIMELINE
           ============================================================== */
        <div className="relative border-l-2 border-blue-500/30 ml-4 pl-6 space-y-5 py-2">
          {filteredTimeline.map((entry, index) => (
            <div key={entry.entry_id || index} className="relative group">
              <div className="absolute -left-[31px] top-2 w-4 h-4 rounded-full bg-slate-900 border-2 border-blue-500 flex items-center justify-center text-[8px] text-blue-300 font-bold shadow-sm">
                {index + 1}
              </div>

              <div
                className="case-card p-4 sm:p-5 rounded-xl space-y-2.5 shadow-sm hover:border-slate-300"
                role="article"
                aria-label={`Event at ${entry.timestamp_display}: ${entry.event_description}`}
              >
                <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-slate-100">
                  <div className="flex items-center space-x-2 text-xs font-bold text-slate-900 font-mono">
                    <Clock className="w-3.5 h-3.5 text-blue-600" aria-hidden="true" />
                    <span>{entry.timestamp_display}</span>
                    {entry.is_uncertain && (
                      <span className="text-[10px] text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full font-sans flex items-center">
                        <AlertCircle className="w-3 h-3 mr-1" aria-hidden="true" /> Approximate Time
                      </span>
                    )}
                  </div>

                  <span className="text-[10px] px-2 py-0.5 rounded-full font-mono uppercase font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                    {entry.document_type}
                  </span>
                </div>

                <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-normal">
                  {entry.event_description}
                </p>

                <div className="flex items-center justify-between flex-wrap gap-2 pt-2 text-[11px] text-slate-500">
                  <div className="flex items-center space-x-3 flex-wrap gap-1">
                    {entry.participants && entry.participants.length > 0 && (
                      <span className="flex items-center text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full font-medium text-[10px] border border-blue-100">
                        <User className="w-3 h-3 mr-1 text-blue-600" aria-hidden="true" />
                        <span>{entry.participants.join(', ')}</span>
                      </span>
                    )}
                    {entry.location && (
                      <span className="flex items-center text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-medium text-[10px] border border-emerald-100">
                        <MapPin className="w-3 h-3 mr-1 text-emerald-600" aria-hidden="true" />
                        <span>{entry.location}</span>
                      </span>
                    )}
                  </div>

                  <span className="flex items-center text-slate-400 font-mono text-[10px]">
                    <FileText className="w-3 h-3 mr-1 text-slate-400" aria-hidden="true" />
                    <span>{entry.document_name}</span>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
