import React, { useEffect, useState, useMemo } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { TimelineEntry } from '../types';
import { Clock, User, MapPin, FileText, AlertCircle, Calendar, Filter, Search, Table, ListTree } from 'lucide-react';

export const TimelinePage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [participantFilter, setParticipantFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [viewMode, setViewMode] = useState<'timeline' | 'table'>('timeline');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeCaseId) return;
    setLoading(true);
    api
      .getTimeline(activeCaseId)
      .then((entries) => setTimeline(entries))
      .catch((e) => console.error(e))
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
          <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
            Module 2 • Chronological Event Reconstruction
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
            Incident Event Timeline
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            <strong>{timeline.length}</strong> sequenced chronological events for case <strong>{activeCase?.name}</strong>.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs">
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

          {/* View Mode Toggle */}
          <div className="flex items-center rounded-lg border border-slate-300 overflow-hidden bg-white shadow-sm p-0.5">
            <button
              onClick={() => setViewMode('timeline')}
              className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-semibold rounded-md transition ${
                viewMode === 'timeline' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ListTree className="w-3.5 h-3.5" />
              <span>Timeline</span>
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-semibold rounded-md transition ${
                viewMode === 'table' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Table className="w-3.5 h-3.5" />
              <span>Table</span>
            </button>
          </div>
        </div>
      </div>

      {timeline.length === 0 ? (
        <div className="case-card p-12 text-center rounded-2xl">
          <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Timeline Generated Yet</h3>
          <p className="text-xs text-slate-500 mt-1">
            Run the investigation analysis pipeline on uploaded documents to extract chronological events.
          </p>
        </div>
      ) : filteredTimeline.length === 0 ? (
        <div className="case-card p-8 text-center rounded-2xl">
          <Filter className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <h4 className="text-base font-bold text-slate-800">No Events Match Filter</h4>
          <p className="text-xs text-slate-500 mt-1">
            Try adjusting your search query or selecting "All People".
          </p>
        </div>
      ) : viewMode === 'table' ? (
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
        <div className="relative border-l-2 border-blue-500/30 ml-4 pl-6 space-y-5 py-2">
          {filteredTimeline.map((entry, index) => (
            <div key={entry.entry_id || index} className="relative group">
              {/* Timeline Node Dot */}
              <div className="absolute -left-[31px] top-2 w-4 h-4 rounded-full bg-slate-900 border-2 border-blue-500 flex items-center justify-center text-[8px] text-blue-300 font-bold shadow-sm">
                {index + 1}
              </div>

              {/* Event Card */}
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

                {/* Event Description */}
                <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-normal">
                  {entry.event_description}
                </p>

                {/* Participants & Location Badges */}
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
