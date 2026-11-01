import React, { useEffect, useState, useMemo } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { TimelineEntry } from '../types';
import { Clock, User, MapPin, FileText, AlertCircle, Calendar, Filter, Search } from 'lucide-react';

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
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
            Chronological Reconstruction (Module 2)
          </div>
          <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
            Incident Event Timeline
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {timeline.length} sequenced chronological events for case <strong>{activeCase?.name}</strong>.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search events or locations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-white border border-gray-300 rounded text-xs text-[#131A2E] focus:outline-none focus:ring-1 focus:ring-[#C9962F] w-48"
              aria-label="Filter timeline events by text"
            />
          </div>

          <select
            value={participantFilter}
            onChange={(e) => setParticipantFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-white border border-gray-300 rounded text-xs text-[#131A2E] font-medium"
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
          <div className="flex items-center rounded border border-gray-300 overflow-hidden bg-white">
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-2.5 py-1 text-xs font-semibold ${
                viewMode === 'timeline' ? 'bg-[#131A2E] text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Timeline
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-2.5 py-1 text-xs font-semibold ${
                viewMode === 'table' ? 'bg-[#131A2E] text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Data Table
            </button>
          </div>
        </div>
      </div>

      {timeline.length === 0 ? (
        <div className="case-card p-12 text-center rounded-lg">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-gray-700">No Timeline Generated Yet</h3>
          <p className="text-xs text-gray-500 mt-1">
            Run the investigation analysis pipeline on uploaded documents to extract chronological events.
          </p>
        </div>
      ) : filteredTimeline.length === 0 ? (
        <div className="case-card p-8 text-center rounded-lg">
          <Filter className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <h4 className="text-sm font-bold text-gray-700">No Events Match Filter</h4>
          <p className="text-xs text-gray-500 mt-1">
            Try adjusting your search query or selecting "All People".
          </p>
        </div>
      ) : viewMode === 'table' ? (
        <div className="case-card p-4 rounded-lg bg-white overflow-x-auto border border-gray-200">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-[#FAF8F3] text-gray-700 font-mono text-[10px] uppercase border-b border-gray-200">
              <tr>
                <th className="p-2.5">#</th>
                <th className="p-2.5">Timestamp</th>
                <th className="p-2.5">Event Description</th>
                <th className="p-2.5">Participants</th>
                <th className="p-2.5">Location</th>
                <th className="p-2.5">Source Document</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-serif">
              {filteredTimeline.map((entry, idx) => (
                <tr key={entry.entry_id || idx} className="hover:bg-amber-50/40">
                  <td className="p-2.5 font-mono text-[10px] text-gray-400">{idx + 1}</td>
                  <td className="p-2.5 font-mono font-bold text-[#131A2E] whitespace-nowrap">
                    {entry.timestamp_display}
                    {entry.is_uncertain && (
                      <span className="ml-1 text-[9px] text-amber-600 bg-amber-50 px-1 py-0.2 rounded font-sans">
                        approx
                      </span>
                    )}
                  </td>
                  <td className="p-2.5 text-[#131A2E] max-w-xs">{entry.event_description}</td>
                  <td className="p-2.5 text-amber-800 whitespace-nowrap font-sans font-medium">
                    {entry.participants && entry.participants.length > 0 ? entry.participants.join(', ') : '—'}
                  </td>
                  <td className="p-2.5 text-emerald-800 whitespace-nowrap font-sans">
                    {entry.location || '—'}
                  </td>
                  <td className="p-2.5 font-mono text-[10px] text-gray-500 whitespace-nowrap">
                    {entry.document_name}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="relative border-l-2 border-[#C9962F]/40 ml-4 pl-6 space-y-6 py-2">
          {filteredTimeline.map((entry, index) => (
            <div key={entry.entry_id || index} className="relative group">
              {/* Timeline Node Dot */}
              <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-[#131A2E] border-2 border-[#C9962F] flex items-center justify-center text-[8px] text-[#C9962F] font-bold">
                {index + 1}
              </div>

              {/* Event Card */}
              <div
                className="case-card p-4 rounded-lg space-y-2"
                role="article"
                aria-label={`Event at ${entry.timestamp_display}: ${entry.event_description}`}
              >
                <div className="flex items-center justify-between flex-wrap gap-2 pb-1.5 border-b border-gray-100">
                  <div className="flex items-center space-x-2 text-xs font-bold text-[#131A2E] font-mono">
                    <Clock className="w-3.5 h-3.5 text-[#C9962F]" aria-hidden="true" />
                    <span>{entry.timestamp_display}</span>
                    {entry.is_uncertain && (
                      <span className="text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.2 rounded font-sans flex items-center">
                        <AlertCircle className="w-2.5 h-2.5 mr-1" aria-hidden="true" /> Approximate Time
                      </span>
                    )}
                  </div>

                  <span className="stamp-label stamp-navy text-[9px]">
                    {entry.document_type}
                  </span>
                </div>

                {/* Event Description */}
                <p className="text-xs text-[#131A2E] font-serif leading-relaxed">
                  {entry.event_description}
                </p>

                {/* Participants & Location Badges */}
                <div className="flex items-center justify-between flex-wrap gap-2 pt-2 text-[11px] text-gray-500">
                  <div className="flex items-center space-x-3">
                    {entry.participants && entry.participants.length > 0 && (
                      <span className="flex items-center text-amber-800">
                        <User className="w-3 h-3 mr-1 text-[#C9962F]" aria-hidden="true" />
                        <span>{entry.participants.join(', ')}</span>
                      </span>
                    )}
                    {entry.location && (
                      <span className="flex items-center text-emerald-800">
                        <MapPin className="w-3 h-3 mr-1 text-emerald-600" aria-hidden="true" />
                        <span>{entry.location}</span>
                      </span>
                    )}
                  </div>

                  <span className="flex items-center text-gray-400 font-mono text-[10px]">
                    <FileText className="w-3 h-3 mr-1" aria-hidden="true" />
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
