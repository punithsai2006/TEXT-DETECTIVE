import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { Hypothesis } from '../types';
import { HypothesisCard } from '../components/HypothesisCard';
import { BrainCircuit, PlusCircle, RefreshCw, AlertCircle, Award } from 'lucide-react';

export const HypothesesPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [rescoring, setRescoring] = useState(false);

  useEffect(() => {
    if (!activeCaseId) return;
    setLoading(true);
    api
      .getHypotheses(activeCaseId)
      .then((items) => setHypotheses(items))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [activeCaseId]);

  const handleAddHypothesis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCaseId || !title.trim()) return;
    try {
      const updated = await api.addHypotheses(activeCaseId, [{ title: title.trim(), description: desc.trim() }]);
      setHypotheses(updated);
      setShowAddModal(false);
      setTitle('');
      setDesc('');
    } catch (err: any) {
      alert(`Failed to add hypothesis: ${err.message}`);
    }
  };

  const handleRescore = async () => {
    if (!activeCaseId) return;
    setRescoring(true);
    try {
      const rescored = await api.rescoreHypotheses(activeCaseId);
      setHypotheses(rescored);
    } catch (err: any) {
      alert(`Rescoring failed: ${err.message}`);
    } finally {
      setRescoring(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-gray-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
            Evidence-Based Hypothesis Ranking (Slide 18)
          </div>
          <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
            Candidate Hypotheses & Explanations
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Comparing competing explanations against retrieved evidence for <strong>{activeCase?.name}</strong>.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleRescore}
            disabled={rescoring}
            className="flex items-center space-x-1.5 px-3 py-1.5 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${rescoring ? 'animate-spin' : ''}`} />
            <span>Rescore Hypotheses</span>
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded bg-[#C9962F] text-[#131A2E] text-xs font-bold hover:bg-[#E0B354] transition shadow"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Candidate Hypothesis</span>
          </button>
        </div>
      </div>

      {/* Slide 18 Scoring Formula Banner */}
      <div className="case-card p-4 rounded-lg bg-[#FAF8F3] border border-[#C9962F]/40 text-xs">
        <div className="flex items-center justify-between pb-1.5 border-b border-gray-200 mb-2">
          <span className="font-serif font-bold text-[#131A2E] uppercase tracking-wide">
            Exact Scoring Algorithm (Slide 18):
          </span>
          <span className="font-mono text-[#C9962F] font-bold">
            Score(H) = Support - Conflict + Corroboration - ConflictPenalty
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-[11px] text-gray-600">
          <div><strong>Support:</strong> Count of evidence chunks agreeing with hypothesis claims.</div>
          <div><strong>Conflict:</strong> Count of evidence chunks disagreeing with claims.</div>
          <div><strong>Corroboration:</strong> +1 bonus per claim supported by 2+ documents & 2+ authors.</div>
          <div><strong>Penalty:</strong> -1 subtracted for each unresolved contradiction.</div>
        </div>
        <div className="mt-2 text-[10px] text-gray-500 italic border-t border-gray-200/60 pt-1.5">
          Forensic Guidance: The hypothesis score is an auditable mathematical ranking heuristic. It is not a probability of truth or legal finding.
        </div>
      </div>

      {/* Hypotheses List */}
      {hypotheses.length === 0 ? (
        <div className="case-card p-12 text-center rounded-lg text-gray-500 text-xs">
          <BrainCircuit className="w-12 h-12 text-gray-300 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-gray-700">No Hypotheses Evaluated Yet</h3>
          <p className="text-xs text-gray-500 mt-1">
            Run the pipeline or click "Add Candidate Hypothesis" to evaluate competing theories.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {hypotheses.map((h) => (
            <HypothesisCard key={h.hypothesis_id} hypothesis={h} />
          ))}
        </div>
      )}

      {/* Add Custom Hypothesis Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-2xl border border-[#C9962F]">
            <div className="flex items-center justify-between pb-3 border-b border-gray-200">
              <h3 className="font-serif font-bold text-base text-[#131A2E]">
                Add Candidate Hypothesis
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-gray-400 hover:text-gray-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddHypothesis} className="mt-4 space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-gray-700 mb-1">
                  Hypothesis Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Subcontractor USB Exfiltration"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded focus:border-[#C9962F] focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">
                  Detailed Explanation / Mechanism *
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="Describe how the event happened, who was involved, and what actions were taken..."
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded focus:border-[#C9962F] focus:outline-none"
                />
              </div>

              <div className="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!title.trim() || !desc.trim()}
                  className="px-4 py-1.5 bg-[#C9962F] text-[#131A2E] font-bold rounded hover:bg-[#E0B354] transition disabled:opacity-50"
                >
                  Score Against Evidence
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
