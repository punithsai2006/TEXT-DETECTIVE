import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { Hypothesis } from '../types';
import { HypothesisCard } from '../components/HypothesisCard';
import { BrainCircuit, AlertCircle, Award, Calculator, Info } from 'lucide-react';

export const HypothesesPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!activeCaseId) return;
    setLoading(true);
    api
      .getHypotheses(activeCaseId)
      .then((items) => setHypotheses(items))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [activeCaseId]);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
            Evidence-Based Hypothesis Ranking
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
            Candidate Hypotheses & Explanations
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Comparing competing explanations against retrieved evidence for <strong>{activeCase?.name}</strong>.
          </p>
        </div>


      </div>

      {/* Slide 18 Scoring Formula Card */}
      <div className="case-card p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm text-xs space-y-3">
        <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 flex-wrap gap-2">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-md bg-blue-50 text-blue-600">
              <Calculator className="w-4 h-4" />
            </div>
            <span className="font-bold text-slate-900 uppercase tracking-wide text-xs">
              Hypothesis Scoring Formula
            </span>
          </div>
          <span className="font-mono text-blue-700 font-bold bg-blue-50 px-3 py-1 rounded-full border border-blue-200 text-xs">
            Score(H) = Support - Conflict + Corroboration - ConflictPenalty
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5 text-[11px]">
          <div className="bg-emerald-50/70 p-2.5 rounded-xl border border-emerald-200/60">
            <strong className="text-emerald-800 block mb-0.5">Support (+)</strong>
            <span className="text-slate-600">Number of evidence chunks explicitly agreeing with hypothesis claims.</span>
          </div>
          <div className="bg-rose-50/70 p-2.5 rounded-xl border border-rose-200/60">
            <strong className="text-rose-800 block mb-0.5">Conflict (-)</strong>
            <span className="text-slate-600">Number of evidence chunks directly contradicting hypothesis claims.</span>
          </div>
          <div className="bg-amber-50/70 p-2.5 rounded-xl border border-amber-200/60">
            <strong className="text-amber-800 block mb-0.5">Corroboration (+)</strong>
            <span className="text-slate-600">+1 multi-source bonus per claim supported by 2+ distinct files and authors.</span>
          </div>
          <div className="bg-purple-50/70 p-2.5 rounded-xl border border-purple-200/60">
            <strong className="text-purple-800 block mb-0.5">Conflict Penalty (-)</strong>
            <span className="text-slate-600">-1 subtracted for each unresolved cross-document contradiction.</span>
          </div>
        </div>

        <div className="text-[10px] text-slate-400 italic pt-2 border-t border-slate-100 flex items-center gap-1.5">
          <Info className="w-3 h-3 text-slate-400 shrink-0" />
          <span>Forensic Ranking Heuristic: Score(H) is an auditable comparative metric for ranking candidate explanations. It does not represent absolute probability or formal legal culpability.</span>
        </div>
      </div>

      {/* Hypotheses List */}
      {hypotheses.length === 0 ? (
        <div className="case-card p-12 text-center rounded-2xl text-slate-500 text-xs">
          <BrainCircuit className="w-12 h-12 text-slate-300 mx-auto mb-2" />
          <h3 className="text-base font-bold text-slate-800">No Hypotheses Evaluated Yet</h3>
          <p className="text-xs text-slate-500 mt-1">
            Run the pipeline or click "Add Candidate" to evaluate competing theories against evidence.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {hypotheses.map((h) => (
            <HypothesisCard key={h.hypothesis_id} hypothesis={h} />
          ))}
        </div>
      )}

    </div>
  );
};
