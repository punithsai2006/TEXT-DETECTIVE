import React, { useState } from 'react';
import { EvidenceItem } from '../types';
import { FileText, User, Clock, Check, Copy, Hash } from 'lucide-react';

interface EvidenceCardProps {
  evidence: EvidenceItem;
  rank?: number;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence, rank }) => {
  const [copied, setCopied] = useState(false);

  const copyCitation = () => {
    const citation = `"${evidence.text}" — Source: ${evidence.document_name} ${evidence.speaker ? `(${evidence.speaker})` : ''} [Sentences: ${evidence.sentence_indices.join(', ')}]`;
    navigator.clipboard.writeText(citation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="case-card p-4 sm:p-5 rounded-xl border border-slate-200/80 shadow-sm relative group hover:border-slate-300">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center space-x-2 flex-wrap gap-1">
          {rank !== undefined && (
            <span className="w-5 h-5 rounded-full bg-slate-900 text-white flex items-center justify-center text-[10px] font-bold font-mono">
              {rank}
            </span>
          )}
          <span className="text-[10px] px-2 py-0.5 rounded-full font-mono uppercase font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            {evidence.document_type}
          </span>
          <span className="text-xs font-semibold text-slate-800 truncate max-w-[220px]" title={evidence.document_name}>
            {evidence.document_name}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[10px] text-slate-600 font-mono bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
            Score: {evidence.score.toFixed(3)}
          </span>
          <button
            onClick={copyCitation}
            className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition"
            title="Copy exact citation"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Excerpt Body */}
      <blockquote className="mt-3 text-xs sm:text-sm text-slate-800 leading-relaxed pl-3.5 border-l-2 border-blue-600 bg-slate-50/70 py-2.5 pr-3 rounded-r-lg font-normal">
        "{evidence.text}"
      </blockquote>

      {/* Source Meta Footer */}
      <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 flex-wrap gap-2">
        <div className="flex items-center space-x-4">
          {evidence.speaker && (
            <span className="flex items-center text-slate-700 font-medium">
              <User className="w-3 h-3 text-blue-600 mr-1" />
              <span>{evidence.speaker}</span>
            </span>
          )}
          {evidence.timestamp && (
            <span className="flex items-center text-slate-500 font-mono">
              <Clock className="w-3 h-3 text-slate-400 mr-1" />
              <span>{evidence.timestamp}</span>
            </span>
          )}
        </div>

        <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
          <Hash className="w-2.5 h-2.5" />
          <span>Sentences: {evidence.sentence_indices.map((i) => `#${i + 1}`).join(', ')}</span>
        </span>
      </div>
    </div>
  );
};
