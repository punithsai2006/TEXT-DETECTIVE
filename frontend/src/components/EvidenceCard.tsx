import React, { useState } from 'react';
import { EvidenceItem } from '../types';
import { FileText, User, Clock, Check, Copy } from 'lucide-react';

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
    <div className="case-card p-4 rounded-lg relative">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center space-x-2">
          {rank !== undefined && (
            <span className="w-5 h-5 rounded-full bg-[#131A2E] text-white flex items-center justify-center text-[10px] font-bold">
              {rank}
            </span>
          )}
          <span className="stamp-label stamp-navy text-[10px]">
            {evidence.document_type}
          </span>
          <span className="text-xs font-semibold text-gray-700 truncate max-w-[200px]" title={evidence.document_name}>
            {evidence.document_name}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[10px] text-gray-500 font-mono bg-gray-100 px-1.5 py-0.5 rounded">
            Score: {evidence.score.toFixed(3)}
          </span>
          <button
            onClick={copyCitation}
            className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition"
            title="Copy exact citation"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Excerpt Body */}
      <blockquote className="mt-2.5 text-xs text-[#131A2E] leading-relaxed pl-3 border-l-2 border-[#C9962F] italic bg-[#FAF8F3]/60 py-1.5 pr-2 rounded-r">
        "{evidence.text}"
      </blockquote>

      {/* Source Meta Footer */}
      <div className="mt-3 pt-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500">
        <div className="flex items-center space-x-4">
          {evidence.speaker && (
            <span className="flex items-center">
              <User className="w-3 h-3 text-[#C9962F] mr-1" />
              <span>{evidence.speaker}</span>
            </span>
          )}
          {evidence.timestamp && (
            <span className="flex items-center">
              <Clock className="w-3 h-3 text-gray-400 mr-1" />
              <span>{evidence.timestamp}</span>
            </span>
          )}
        </div>

        <span className="text-[10px] text-gray-400">
          Sentences: {evidence.sentence_indices.map((i) => `#${i + 1}`).join(', ')}
        </span>
      </div>
    </div>
  );
};
