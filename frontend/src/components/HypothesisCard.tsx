import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { SourceCitation } from './SourceCitation';
import { Hypothesis } from '../types';
import { Award, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, XCircle, FileText, Check } from 'lucide-react';

interface HypothesisCardProps {
  hypothesis: Hypothesis;
}

export const HypothesisCard: React.FC<HypothesisCardProps> = ({ hypothesis }) => {
  const [expanded, setExpanded] = useState(false);

  if (hypothesis.score_method_version) return <article className="case-card p-5 rounded-2xl border border-slate-200 space-y-4">
    <div className="flex justify-between gap-4"><div>
      <h3 className="text-lg font-bold">{hypothesis.title}</h3>
      <p className="text-sm text-slate-600 mt-2">{hypothesis.description}</p>
      {hypothesis.description_source_span_ids?.map(id => <div key={id}><SourceCitation spanId={id} label="Sources for this proposed interpretation" /></div>)}
    </div><strong className="text-xl whitespace-nowrap">{hypothesis.evidence_support_score == null ? 'Not scored' : hypothesis.evidence_support_score.toFixed(3)}</strong></div>
    <p className="text-xs text-amber-800">Evidence-support score — not a probability of guilt. {hypothesis.score_method_version}</p>
    {hypothesis.is_proposed_explanation && <p className="text-sm font-semibold text-blue-700">Most supported qualified interpretation; human review required.</p>}
    {hypothesis.score_breakdown?.weights && <div className="overflow-auto"><table className="text-xs w-full text-left"><thead><tr><th>Component</th><th>Normalized input</th><th>Weight</th><th>Contribution</th></tr></thead><tbody>
      {(['support', 'conflict', 'temporal', 'relationships', 'coverage', 'assumptions'] as const).map(key => <tr className="border-t" key={key}>
        <td className="py-2 capitalize">{key}</td><td>{hypothesis.score_breakdown![key].toFixed(3)}</td><td>{hypothesis.score_breakdown!.weights[key]}</td><td>{hypothesis.score_breakdown!.weighted_components[key].toFixed(3)}</td>
      </tr>)}
    </tbody></table><p className="text-xs text-slate-500">{hypothesis.score_breakdown.distinct_lineage_count} distinct text lineages; repeated passages and graph projections add no corroboration bonus.</p></div>}
    <div className="grid md:grid-cols-2 gap-4 text-sm"><div><h4 className="font-semibold">Supporting passages</h4>{hypothesis.supporting_source_span_ids?.length ? hypothesis.supporting_source_span_ids.map(id => <div key={id}><SourceCitation spanId={id} /></div>) : <p>None established.</p>}</div>
      <div><h4 className="font-semibold">Contrary passages</h4>{hypothesis.contrary_source_span_ids?.length ? hypothesis.contrary_source_span_ids.map(id => <div key={id}><SourceCitation spanId={id} /></div>) : <p>None established.</p>}</div></div>
    <p className="text-xs"><strong>Assumptions:</strong> {hypothesis.assumptions?.join('; ') || 'None reported'}</p>
    {!!hypothesis.necessary_claims?.length && <details className="text-xs"><summary className="cursor-pointer font-semibold">Inspect necessary claims and assessments</summary>
      {hypothesis.necessary_claims.map(requirement => <div key={requirement.requirement_id} className="border-t py-2"><p>{requirement.text}</p><p className="text-slate-500">{hypothesis.requirement_assessments?.find(a => a.requirement_id === requirement.requirement_id)?.explanation}</p></div>)}
    </details>}
    <p className="text-xs"><strong>Missing evidence:</strong> {hypothesis.missing_evidence?.join('; ') || 'Review evidence coverage'}</p>
    {!hypothesis.is_other && <div className="flex gap-4 text-xs"><Link className="text-blue-700 underline" to={`/graph?hypothesis_id=${encodeURIComponent(hypothesis.hypothesis_id)}`}>Explore connected evidence</Link><Link className="text-blue-700 underline" to={`/timeline?hypothesis_id=${encodeURIComponent(hypothesis.hypothesis_id)}`}>Inspect relevant timeline</Link></div>}
  </article>;

  return (
    <div
      className={`case-card p-5 sm:p-6 rounded-2xl border transition-all ${
        hypothesis.is_proposed_explanation
          ? 'ring-2 ring-blue-600 border-blue-400 shadow-md bg-gradient-to-b from-blue-50/20 via-white to-white'
          : 'border-slate-200/80 shadow-sm'
      }`}
    >
      {/* Proposed Explanation Spotlight Banner */}
      {hypothesis.is_proposed_explanation && (
        <div className="mb-4 flex items-center justify-between bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2 rounded-xl text-xs text-white font-semibold shadow-sm">
          <div className="flex items-center space-x-2">
            <Award className="w-4 h-4 text-amber-300" />
            <span className="uppercase tracking-wider">Proposed Explanation (Rank #1)</span>
          </div>
          <span className="text-[11px] font-normal text-blue-100 hidden sm:inline">
            Highest Net Evidence Score under Hypothesis Scoring Formula
          </span>
        </div>
      )}

      {/* Uncertainty Warning */}
      {hypothesis.uncertainty_warning && (
        <div className="mb-3 flex items-start space-x-2 bg-amber-50 border border-amber-200/80 p-3 rounded-xl text-xs text-amber-800">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{hypothesis.uncertainty_warning}</span>
        </div>
      )}

      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <span className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center text-xs font-bold font-mono shadow-sm">
              #{hypothesis.rank}
            </span>
            <h3 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
              {hypothesis.title}
            </h3>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-mono border border-slate-200">
              {hypothesis.origin}
            </span>
          </div>
          <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed max-w-2xl">
            {hypothesis.description}
          </p>
        </div>

        {/* Total Score Pill */}
        <div className="text-right shrink-0 bg-slate-50 border border-slate-200 px-3.5 py-2 rounded-xl">
          <div className="text-2xl font-black text-slate-900 font-mono leading-none">
            {hypothesis.total_score}
          </div>
          <div className="text-[9px] uppercase font-bold text-slate-400 tracking-wider mt-1">
            Net Score
          </div>
        </div>
      </div>

      {/* Slide 18 Scoring Formula Breakdown */}
      <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-xs">
        <div className="bg-emerald-50/70 p-2.5 rounded-xl border border-emerald-200/80">
          <div className="text-[10px] uppercase font-bold text-emerald-800">Support (+)</div>
          <div className="text-lg font-bold text-emerald-600 font-mono mt-0.5">
            {hypothesis.support_score}
          </div>
          <div className="text-[9px] text-emerald-700 font-medium">Agreeing Chunks</div>
        </div>

        <div className="bg-rose-50/70 p-2.5 rounded-xl border border-rose-200/80">
          <div className="text-[10px] uppercase font-bold text-rose-800">Conflict (-)</div>
          <div className="text-lg font-bold text-rose-600 font-mono mt-0.5">
            {hypothesis.conflict_score}
          </div>
          <div className="text-[9px] text-rose-700 font-medium">Conflicting Chunks</div>
        </div>

        <div className="bg-amber-50/70 p-2.5 rounded-xl border border-amber-200/80">
          <div className="text-[10px] uppercase font-bold text-amber-800">Corroboration (+)</div>
          <div className="text-lg font-bold text-amber-600 font-mono mt-0.5">
            +{hypothesis.corroboration_score}
          </div>
          <div className="text-[9px] text-amber-700 font-medium">Cross-Doc Bonus</div>
        </div>

        <div className="bg-purple-50/70 p-2.5 rounded-xl border border-purple-200/80">
          <div className="text-[10px] uppercase font-bold text-purple-800">Penalty (-)</div>
          <div className="text-lg font-bold text-purple-600 font-mono mt-0.5">
            -{hypothesis.conflict_penalty}
          </div>
          <div className="text-[9px] text-purple-700 font-medium">Unresolved Conflicts</div>
        </div>

        <div className="col-span-2 sm:col-span-1 bg-slate-900 text-white p-2.5 rounded-xl flex flex-col justify-center items-center shadow-sm">
          <div className="text-[10px] uppercase font-bold text-blue-400">Total Formula</div>
          <div className="text-lg font-bold text-white font-mono mt-0.5">
            = {hypothesis.total_score}
          </div>
          <div className="text-[9px] text-slate-400 font-medium">Net Evaluation</div>
        </div>
      </div>

      {/* Claims Toggle */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center text-xs font-semibold text-slate-800 hover:text-blue-600 transition"
        >
          <span>{expanded ? 'Hide' : 'Inspect'} Claims Breakdown ({hypothesis.claims.length} verifiable claims)</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5 ml-1 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 ml-1 text-slate-400" />}
        </button>
        <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">
          Score(H) = Support - Conflict + Corroboration - ConflictPenalty
        </span>
      </div>

      {/* Expanded Claims List */}
      {expanded && (
        <div className="mt-3 space-y-2.5 border-t border-slate-100 pt-3">
          {hypothesis.claims.map((claim, idx) => (
            <div key={claim.claim_id || idx} className="bg-slate-50 p-3.5 rounded-xl text-xs border border-slate-200/70">
              <div className="flex items-start justify-between gap-3">
                <div className="font-medium text-slate-800 max-w-xl leading-relaxed">
                  <span className="font-bold text-slate-900 mr-1.5">{idx + 1}.</span>
                  "{claim.text}"
                </div>
                {claim.is_corroborated ? (
                  <span className="flex items-center text-[10px] font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full shrink-0 border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3 mr-1" /> Corroborated (+1)
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-500 bg-slate-200/80 px-2 py-0.5 rounded-full shrink-0">
                    Single Source
                  </span>
                )}
              </div>

              <div className="mt-2.5 pt-2 border-t border-slate-200/50 text-[11px] text-slate-500 flex flex-wrap items-center gap-4">
                <span>Supporting Chunks: <strong className="text-slate-700 font-mono">{claim.supporting_evidence_ids.length}</strong></span>
                <span>Conflicting Chunks: <strong className="text-rose-600 font-mono">{claim.conflicting_evidence_ids.length}</strong></span>
                <span>Sources: <strong className="text-slate-700">{claim.contributing_documents.join(', ') || 'None'}</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
