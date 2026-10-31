import React, { useState } from 'react';
import { Hypothesis } from '../types';
import { Award, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

interface HypothesisCardProps {
  hypothesis: Hypothesis;
}

export const HypothesisCard: React.FC<HypothesisCardProps> = ({ hypothesis }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`case-card p-5 rounded-lg border-2 transition ${
        hypothesis.is_proposed_explanation
          ? 'border-[#C9962F] bg-gradient-to-b from-[#FFFDF9] to-white shadow-md'
          : 'border-[#E2DDD0]'
      }`}
    >
      {/* Proposed Explanation Banner */}
      {hypothesis.is_proposed_explanation && (
        <div className="mb-3 flex items-center justify-between bg-[#C9962F]/15 border border-[#C9962F]/40 px-3 py-1.5 rounded text-xs text-[#996F19] font-serif font-bold">
          <div className="flex items-center space-x-1.5">
            <Award className="w-4 h-4 text-[#C9962F]" />
            <span className="uppercase tracking-wider">System's Proposed Explanation</span>
          </div>
          <span className="font-sans text-[11px] font-normal text-gray-600">
            Rank #1 (Highest Net Evidence Score)
          </span>
        </div>
      )}

      {/* Uncertainty Warning */}
      {hypothesis.uncertainty_warning && (
        <div className="mb-3 flex items-start space-x-2 bg-amber-50 border border-amber-200 p-2.5 rounded text-xs text-amber-800">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <span>{hypothesis.uncertainty_warning}</span>
        </div>
      )}

      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <span className="w-6 h-6 rounded-full bg-[#131A2E] text-white flex items-center justify-center text-xs font-bold font-mono">
              #{hypothesis.rank}
            </span>
            <h3 className="text-base font-bold text-[#131A2E] font-serif">
              {hypothesis.title}
            </h3>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-gray-100 text-gray-600 font-mono">
              {hypothesis.origin}
            </span>
          </div>
          <p className="mt-1.5 text-xs text-gray-700 leading-relaxed max-w-2xl">
            {hypothesis.description}
          </p>
        </div>

        {/* Total Score Circle */}
        <div className="text-right">
          <div className="text-2xl font-black text-[#131A2E] font-mono">
            {hypothesis.total_score}
          </div>
          <div className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
            Net Score
          </div>
        </div>
      </div>

      {/* Slide 18 Scoring Formula Breakdown */}
      <div className="mt-4 pt-3 border-t border-gray-100 grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-xs">
        <div className="bg-[#FAF8F3] p-2 rounded border border-emerald-200">
          <div className="text-[10px] uppercase font-bold text-emerald-800">Support (+)</div>
          <div className="text-lg font-bold text-emerald-600 font-mono mt-0.5">
            {hypothesis.support_score}
          </div>
          <div className="text-[9px] text-gray-500">Agreeing Chunks</div>
        </div>

        <div className="bg-[#FAF8F3] p-2 rounded border border-red-200">
          <div className="text-[10px] uppercase font-bold text-red-800">Conflict (-)</div>
          <div className="text-lg font-bold text-red-600 font-mono mt-0.5">
            {hypothesis.conflict_score}
          </div>
          <div className="text-[9px] text-gray-500">Conflicting Chunks</div>
        </div>

        <div className="bg-[#FAF8F3] p-2 rounded border border-amber-200">
          <div className="text-[10px] uppercase font-bold text-amber-800">Corroboration (+)</div>
          <div className="text-lg font-bold text-amber-600 font-mono mt-0.5">
            +{hypothesis.corroboration_score}
          </div>
          <div className="text-[9px] text-gray-500">Multi-Source Bonus</div>
        </div>

        <div className="bg-[#FAF8F3] p-2 rounded border border-purple-200">
          <div className="text-[10px] uppercase font-bold text-purple-800">Penalty (-)</div>
          <div className="text-lg font-bold text-purple-600 font-mono mt-0.5">
            -{hypothesis.conflict_penalty}
          </div>
          <div className="text-[9px] text-gray-500">Unresolved Conflicts</div>
        </div>

        <div className="col-span-2 sm:col-span-1 bg-[#131A2E] text-white p-2 rounded flex flex-col justify-center items-center shadow-inner">
          <div className="text-[10px] uppercase font-bold text-[#E0B354]">Formula Result</div>
          <div className="text-lg font-bold text-white font-mono mt-0.5">
            = {hypothesis.total_score}
          </div>
        </div>
      </div>

      {/* Claims Toggle */}
      <div className="mt-4 pt-2 border-t border-gray-100 flex items-center justify-between">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center text-xs font-semibold text-[#131A2E] hover:text-[#C9962F] transition"
        >
          <span>{expanded ? 'Hide' : 'Inspect'} Claims Breakdown ({hypothesis.claims.length} verifiable claims)</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5 ml-1" /> : <ChevronDown className="w-3.5 h-3.5 ml-1" />}
        </button>
        <span className="text-[11px] text-gray-400 font-mono">
          Score(H) = Support - Conflict + Corroboration - Penalty
        </span>
      </div>

      {/* Expanded Claims List */}
      {expanded && (
        <div className="mt-3 space-y-2 border-t border-gray-100 pt-3">
          {hypothesis.claims.map((claim, idx) => (
            <div key={claim.claim_id || idx} className="bg-[#FAF8F3] p-3 rounded text-xs border border-gray-200">
              <div className="flex items-start justify-between">
                <div className="font-medium text-[#131A2E] max-w-xl">
                  {idx + 1}. "{claim.text}"
                </div>
                {claim.is_corroborated ? (
                  <span className="flex items-center text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                    <CheckCircle2 className="w-3 h-3 mr-1" /> Corroborated (+1)
                  </span>
                ) : (
                  <span className="text-[10px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                    Single / Unverified Source
                  </span>
                )}
              </div>

              <div className="mt-2 text-[11px] text-gray-600 flex items-center space-x-4">
                <span>Supporting evidence: <strong>{claim.supporting_evidence_ids.length}</strong></span>
                <span>Conflicting evidence: <strong>{claim.conflicting_evidence_ids.length}</strong></span>
                <span>Sources: <strong>{claim.contributing_documents.join(', ') || 'None'}</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
