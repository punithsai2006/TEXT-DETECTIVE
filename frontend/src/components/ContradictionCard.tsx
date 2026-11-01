import React from 'react';
import { ContradictionItem, ReviewStatus } from '../types';
import { AlertTriangle, CheckCircle, Scale, User, FileText, CheckSquare, XCircle, HelpCircle, Clock } from 'lucide-react';

interface ContradictionCardProps {
  item: ContradictionItem;
  index: number;
  onUpdateReview?: (id: string, newStatus: ReviewStatus, notes?: string) => void;
}

export const ContradictionCard: React.FC<ContradictionCardProps> = ({ item, index, onUpdateReview }) => {
  const isConflict =
    item.contradiction_type === 'confirmed_contradiction' ||
    item.contradiction_type === 'possible_contradiction';

  const reviewStatus = item.review_status || 'pending_review';

  return (
    <div
      className={`case-card p-4 rounded-lg border-l-4 ${isConflict ? 'border-l-red-600' : 'border-l-emerald-600'}`}
      role="article"
      aria-label={`Discrepancy ${index} concerning ${item.entity_event_link}`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-gray-100">
        <div className="flex items-center space-x-2">
          {isConflict ? (
            <AlertTriangle className="w-4 h-4 text-red-600" aria-hidden="true" />
          ) : (
            <CheckCircle className="w-4 h-4 text-emerald-600" aria-hidden="true" />
          )}
          <span className="font-bold text-xs uppercase tracking-wider text-[#131A2E]">
            Discrepancy #{index}: {item.entity_event_link}
          </span>
        </div>

        <div className="flex items-center flex-wrap gap-2">
          {/* Review Status Badge */}
          <span
            className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase font-semibold ${
              reviewStatus === 'confirmed'
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : reviewStatus === 'rejected'
                ? 'bg-rose-100 text-rose-800 border border-rose-300'
                : reviewStatus === 'needs_further_investigation'
                ? 'bg-amber-100 text-amber-800 border border-amber-300'
                : 'bg-gray-100 text-gray-700 border border-gray-300'
            }`}
          >
            Review: {reviewStatus.replace(/_/g, ' ')}
          </span>

          {/* Detection Engine Badge */}
          <span
            className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase font-semibold ${
              item.detection_engine === 'nli'
                ? 'bg-blue-100 text-blue-800 border border-blue-300'
                : item.detection_engine === 'llm_verified'
                ? 'bg-purple-100 text-purple-800 border border-purple-300'
                : 'bg-amber-50 text-amber-900 border border-amber-300'
            }`}
            title={`Detection Engine: ${item.detection_engine || 'rules'}`}
          >
            Engine: {item.detection_engine === 'nli' ? 'NLI Model' : item.detection_engine === 'llm_verified' ? 'LLM Judge' : 'Rules'}
          </span>

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
          <span className="text-[10px] text-gray-500 font-mono" title="Heuristic ranking confidence, not mathematical probability">
            Conf: {(item.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Side-by-side statements comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-3 text-xs">
        {/* Statement A */}
        <div className="bg-[#FAF8F3] p-3 rounded border border-gray-200">
          <div className="flex items-center justify-between text-[11px] text-gray-500 mb-1.5 font-medium">
            <span className="flex items-center">
              <FileText className="w-3 h-3 text-[#131A2E] mr-1" aria-hidden="true" />
              <strong className="text-gray-700">{item.doc_a_name}</strong>
            </span>
            {item.speaker_a && (
              <span className="flex items-center text-[#C9962F]">
                <User className="w-3 h-3 mr-1" aria-hidden="true" />
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
              <FileText className="w-3 h-3 text-[#131A2E] mr-1" aria-hidden="true" />
              <strong className="text-gray-700">{item.doc_b_name}</strong>
            </span>
            {item.speaker_b && (
              <span className="flex items-center text-[#C9962F]">
                <User className="w-3 h-3 mr-1" aria-hidden="true" />
                {item.speaker_b}
              </span>
            )}
          </div>
          <p className="italic text-[#131A2E] leading-relaxed">
            "{item.statement_b}"
          </p>
        </div>
      </div>

      {/* Analysis explanation & Model source */}
      <div className="pt-2 text-xs text-gray-600 space-y-1.5">
        <div className="flex items-start space-x-2">
          <Scale className="w-4 h-4 text-[#C9962F] shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <span className="font-semibold text-[#131A2E]">Analysis: </span>
            <span>{item.explanation}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between text-[11px] text-gray-500 pt-1 border-t border-gray-100">
          <span className="font-mono text-[10px]">
            Model: {item.calculation_source || 'cross_encoder_nli_and_conflict_rules'}
          </span>

          {item.reviewer_id && (
            <span className="flex items-center text-gray-500 text-[10px]">
              <Clock className="w-3 h-3 mr-1" aria-hidden="true" />
              Verified by {item.reviewer_id} {item.review_notes ? `(${item.review_notes})` : ''}
            </span>
          )}

          {/* Interactive human review actions */}
          {onUpdateReview && (
            <div className="flex items-center space-x-1 mt-1 sm:mt-0">
              <button
                onClick={() => onUpdateReview(item.id, 'confirmed', 'Analyst verified')}
                className="px-2 py-0.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 rounded text-[10px] flex items-center font-medium"
                aria-label="Confirm contradiction"
              >
                <CheckSquare className="w-2.5 h-2.5 mr-0.5" /> Confirm
              </button>
              <button
                onClick={() => onUpdateReview(item.id, 'rejected', 'Analyst rejected')}
                className="px-2 py-0.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 rounded text-[10px] flex items-center font-medium"
                aria-label="Reject contradiction"
              >
                <XCircle className="w-2.5 h-2.5 mr-0.5" /> Reject
              </button>
              <button
                onClick={() => onUpdateReview(item.id, 'needs_further_investigation', 'Requires secondary evidence')}
                className="px-2 py-0.5 bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-300 rounded text-[10px] flex items-center font-medium"
                aria-label="Flag contradiction for further investigation"
              >
                <HelpCircle className="w-2.5 h-2.5 mr-0.5" /> Investigate
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
