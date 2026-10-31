import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { TimelineEntry } from '../types';
import { Clock, User, MapPin, FileText, AlertCircle, Calendar } from 'lucide-react';

export const TimelinePage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
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

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
          Chronological Reconstruction
        </div>
        <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
          Incident Event Timeline
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          {timeline.length} sequenced chronological events for case <strong>{activeCase?.name}</strong>.
        </p>
      </div>

      {timeline.length === 0 ? (
        <div className="case-card p-12 text-center rounded-lg">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-gray-700">No Timeline Generated Yet</h3>
          <p className="text-xs text-gray-500 mt-1">
            Run the investigation analysis pipeline on uploaded documents to extract chronological events.
          </p>
        </div>
      ) : (
        <div className="relative border-l-2 border-[#C9962F]/40 ml-4 pl-6 space-y-6 py-2">
          {timeline.map((entry, index) => (
            <div key={entry.entry_id || index} className="relative group">
              {/* Timeline Node Dot */}
              <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-[#131A2E] border-2 border-[#C9962F] flex items-center justify-center text-[8px] text-[#C9962F] font-bold">
                {index + 1}
              </div>

              {/* Event Card */}
              <div className="case-card p-4 rounded-lg space-y-2">
                <div className="flex items-center justify-between flex-wrap gap-2 pb-1.5 border-b border-gray-100">
                  <div className="flex items-center space-x-2 text-xs font-bold text-[#131A2E] font-mono">
                    <Clock className="w-3.5 h-3.5 text-[#C9962F]" />
                    <span>{entry.timestamp_display}</span>
                    {entry.is_uncertain && (
                      <span className="text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.2 rounded font-sans flex items-center">
                        <AlertCircle className="w-2.5 h-2.5 mr-1" /> Approximate Time
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
                        <User className="w-3 h-3 mr-1 text-[#C9962F]" />
                        <span>{entry.participants.join(', ')}</span>
                      </span>
                    )}
                    {entry.location && (
                      <span className="flex items-center text-emerald-800">
                        <MapPin className="w-3 h-3 mr-1 text-emerald-600" />
                        <span>{entry.location}</span>
                      </span>
                    )}
                  </div>

                  <span className="flex items-center text-gray-400 font-mono text-[10px]">
                    <FileText className="w-3 h-3 mr-1" />
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
