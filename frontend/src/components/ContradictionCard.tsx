import React from 'react';
import { ContradictionItem, ReviewStatus } from '../types';
import { AlertTriangle, CheckCircle, Scale, User, FileText, CheckSquare, XCircle, HelpCircle, Clock, Cpu } from 'lucide-react';

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
      className={`case-card p-5 rounded-xl border-l-4 ${
        item.contradiction_type === 'confirmed_contradiction'
          ? 'border-l-rose-600'
          : item.contradiction_type === 'possible_contradiction'
          ? 'border-l-amber-500'
          : 'border-l-emerald-600'
      } shadow-sm`}
      role="article"
      aria-label={`Discrepancy ${index} concerning ${item.entity_event_link}`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          {isConflict ? (
            <div className="p-1 rounded-md bg-rose-50 text-rose-600">
              <AlertTriangle className="w-4 h-4" aria-hidden="true" />
            </div>
          ) : (
            <div className="p-1 rounded-md bg-emerald-50 text-emerald-600">
              <CheckCircle className="w-4 h-4" aria-hidden="true" />
            </div>
          )}
          <span className="font-bold text-xs uppercase tracking-wider text-slate-900">
            Discrepancy #{index}: {item.entity_event_link}
          </span>
        </div>

        <div className="flex items-center flex-wrap gap-2">
          {/* Review Status Badge */}
          <span
            className={`text-[10px] px-2.5 py-0.5 rounded-full font-mono uppercase font-semibold ${
              reviewStatus === 'confirmed'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : reviewStatus === 'rejected'
                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                : reviewStatus === 'needs_further_investigation'
                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                : 'bg-slate-100 text-slate-700 border border-slate-200'
            }`}
          >
            Review: {reviewStatus.replace(/_/g, ' ')}
          </span>

          {/* Detection Engine Badge */}
          <span
            className="text-[10px] px-2 py-0.5 rounded-full font-mono uppercase font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1"
            title={`Detection Engine: ${item.detection_engine || 'rules'}`}
          >
            <Cpu className="w-3 h-3" />
            <span>{item.detection_engine === 'nli' ? 'NLI DeBERTa' : item.detection_engine === 'llm_verified' ? 'LLM Judge' : 'Rule Engine'}</span>
          </span>

          <span
            className={`text-[10px] px-2.5 py-0.5 rounded-full font-semibold uppercase tracking-wider ${
              item.contradiction_type === 'confirmed_contradiction'
                ? 'bg-rose-100 text-rose-800 border border-rose-200'
                : item.contradiction_type === 'possible_contradiction'
                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
            }`}
          >
            {item.contradiction_type.replace(/_/g, ' ')}
          </span>
          <span className="text-[11px] text-slate-500 font-mono font-medium">
            Conf: {(item.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Side-by-side statements comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-3.5 text-xs">
        {/* Statement A */}
        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
          <div className="flex items-center justify-between text-[11px] text-slate-500 mb-2 font-medium">
            <span className="flex items-center">
              <FileText className="w-3.5 h-3.5 text-slate-600 mr-1.5" aria-hidden="true" />
              <strong className="text-slate-800 font-semibold">{item.doc_a_name}</strong>
            </span>
            {item.speaker_a && (
              <span className="flex items-center px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full font-medium text-[10px]">
                <User className="w-3 h-3 mr-1" aria-hidden="true" />
                {item.speaker_a}
              </span>
            )}
          </div>
          <p className="text-slate-800 leading-relaxed font-normal bg-white p-2.5 rounded-lg border border-slate-200/50">
            "{item.statement_a}"
          </p>
        </div>

        {/* Statement B */}
        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
          <div className="flex items-center justify-between text-[11px] text-slate-500 mb-2 font-medium">
            <span className="flex items-center">
              <FileText className="w-3.5 h-3.5 text-slate-600 mr-1.5" aria-hidden="true" />
              <strong className="text-slate-800 font-semibold">{item.doc_b_name}</strong>
            </span>
            {item.speaker_b && (
              <span className="flex items-center px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full font-medium text-[10px]">
                <User className="w-3 h-3 mr-1" aria-hidden="true" />
                {item.speaker_b}
              </span>
            )}
          </div>
          <p className="text-slate-800 leading-relaxed font-normal bg-white p-2.5 rounded-lg border border-slate-200/50">
            "{item.statement_b}"
          </p>
        </div>
      </div>

      {/* Analysis explanation & Model source */}
      <div className="pt-2 text-xs text-slate-600 space-y-2">
        <div className="flex items-start space-x-2 bg-blue-50/50 p-2.5 rounded-lg border border-blue-100">
          <Scale className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" aria-hidden="true" />
          <div className="text-slate-700">
            <span className="font-semibold text-slate-900">Analysis: </span>
            <span>{item.explanation}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
          <span className="font-mono text-[10px] text-slate-400">
            Model: {item.calculation_source || 'cross_encoder_nli_and_conflict_rules'}
          </span>

          {item.reviewer_id && (
            <span className="flex items-center text-slate-500 text-[10px]">
              <Clock className="w-3 h-3 mr-1" aria-hidden="true" />
              Verified by {item.reviewer_id} {item.review_notes ? `(${item.review_notes})` : ''}
            </span>
          )}

          {/* Interactive human review actions */}
          {onUpdateReview && (
            <div className="flex items-center space-x-1.5 mt-2 sm:mt-0">
              <button
                onClick={() => onUpdateReview(item.id, 'confirmed', 'Analyst verified')}
                className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-lg text-[10px] flex items-center font-medium transition"
                aria-label="Confirm contradiction"
              >
                <CheckSquare className="w-3 h-3 mr-1" /> Confirm
              </button>
              <button
                onClick={() => onUpdateReview(item.id, 'rejected', 'Analyst rejected')}
                className="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-[10px] flex items-center font-medium transition"
                aria-label="Reject contradiction"
              >
                <XCircle className="w-3 h-3 mr-1" /> Dismiss / Reject
              </button>
              <button
                onClick={() => onUpdateReview(item.id, 'needs_further_investigation', 'Requires secondary evidence')}
                className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 rounded-lg text-[10px] flex items-center font-medium transition"
                aria-label="Flag contradiction for further investigation"
              >
                <HelpCircle className="w-3 h-3 mr-1" /> Further Review
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
