import React from 'react';
import { ContradictionItem } from '../types';
import { AlertTriangle, CheckCircle, Scale, User, FileText } from 'lucide-react';

interface ContradictionCardProps {
  item: ContradictionItem;
  index: number;
}

export const ContradictionCard: React.FC<ContradictionCardProps> = ({ item, index }) => {
  const isConflict =
    item.contradiction_type === 'confirmed_contradiction' ||
    item.contradiction_type === 'possible_contradiction';

  return (
    <div className={`case-card p-4 rounded-lg border-l-4 ${isConflict ? 'border-l-red-600' : 'border-l-emerald-600'}`}>
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-gray-100">
        <div className="flex items-center space-x-2">
          {isConflict ? (
            <AlertTriangle className="w-4 h-4 text-red-600" />
          ) : (
            <CheckCircle className="w-4 h-4 text-emerald-600" />
          )}
          <span className="font-bold text-xs uppercase tracking-wider text-[#131A2E]">
            Discrepancy #{index}: {item.entity_event_link}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span
            className={`stamp-label text-[10px] ${
              item.contradiction_type === 'confirmed_contradiction'
                ? 'stamp-danger'
                : item.contradiction_type === 'possible_contradiction'
                ? 'stamp-gold'
                : 'stamp-success'
            }`}
          >
            {item.contradiction_type.replace(/_/g, ' ')}
          </span>
          <span className="text-[10px] text-gray-400 font-mono">
            Confidence: {(item.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Side-by-side statements comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-3 text-xs">
        {/* Statement A */}
        <div className="bg-[#FAF8F3] p-3 rounded border border-gray-200">
          <div className="flex items-center justify-between text-[11px] text-gray-500 mb-1.5 font-medium">
            <span className="flex items-center">
              <FileText className="w-3 h-3 text-[#131A2E] mr-1" />
              <strong className="text-gray-700">{item.doc_a_name}</strong>
            </span>
            {item.speaker_a && (
              <span className="flex items-center text-[#C9962F]">
                <User className="w-3 h-3 mr-1" />
                {item.speaker_a}
              </span>
            )}
          </div>
          <p className="italic text-[#131A2E] leading-relaxed">
            "{item.statement_a}"
          </p>
        </div>

        {/* Statement B */}
        <div className="bg-[#FAF8F3] p-3 rounded border border-gray-200">
          <div className="flex items-center justify-between text-[11px] text-gray-500 mb-1.5 font-medium">
            <span className="flex items-center">
              <FileText className="w-3 h-3 text-[#131A2E] mr-1" />
              <strong className="text-gray-700">{item.doc_b_name}</strong>
            </span>
            {item.speaker_b && (
              <span className="flex items-center text-[#C9962F]">
                <User className="w-3 h-3 mr-1" />
                {item.speaker_b}
              </span>
            )}
          </div>
          <p className="italic text-[#131A2E] leading-relaxed">
            "{item.statement_b}"
          </p>
        </div>
      </div>

      {/* Analysis explanation */}
      <div className="pt-2 text-xs text-gray-600 flex items-start space-x-2">
        <Scale className="w-4 h-4 text-[#C9962F] shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-[#131A2E]">Investigator Analysis: </span>
          <span>{item.explanation}</span>
          <span className="ml-2 inline-block px-1.5 py-0.2 rounded text-[10px] uppercase font-mono bg-gray-100 text-gray-600">
            Status: {item.resolution_status}
          </span>
        </div>
      </div>
    </div>
  );
};
