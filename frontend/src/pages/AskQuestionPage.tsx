import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { AskQuestionResponse } from '../types';
import { EvidenceCard } from '../components/EvidenceCard';
import { HelpCircle, Send, Sparkles, AlertCircle, ShieldCheck, FileText } from 'lucide-react';

export const AskQuestionPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<AskQuestionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sampleQuestions = [
    'Where was Alice Vance located between 10:00 PM and midnight?',
    'Did anyone enter Server Room B with a physical USB flash drive?',
    'What was discovered regarding the lock on the secure door?',
    'Who saw Bob Chen leave his keycard on the table?',
  ];

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCaseId || !question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await api.askQuestion(activeCaseId, question.trim(), 5);
      setResponse(resp);
    } catch (err: any) {
      setError(err.message || 'Failed to answer question');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
          Evidence-Grounded Inquiry
        </div>
        <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
          Ask an Investigative Question
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Queries verified evidence in case <strong>{activeCase?.name}</strong>. Never hallucinates citations or unverified facts.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded text-xs flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Question Form */}
      <div className="case-card p-5 rounded-lg space-y-3">
        <form onSubmit={handleAsk} className="flex gap-2">
          <input
            type="text"
            required
            placeholder="Type your investigative question..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="flex-1 p-2.5 text-xs border border-gray-300 rounded-lg focus:border-[#C9962F] focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="px-5 py-2.5 bg-[#C9962F] text-[#131A2E] text-xs font-bold rounded-lg hover:bg-[#E0B354] transition shadow flex items-center space-x-1.5 disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{loading ? 'Consulting Dossier...' : 'Ask Question'}</span>
          </button>
        </form>

        {/* Quick Question Chips */}
        <div className="flex items-center space-x-1.5 flex-wrap gap-1 text-[11px] text-gray-500">
          <span className="font-semibold text-gray-700 flex items-center">
            <Sparkles className="w-3 h-3 text-[#C9962F] mr-1" /> Suggestions:
          </span>
          {sampleQuestions.map((q, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setQuestion(q)}
              className="px-2 py-0.5 rounded bg-gray-100 hover:bg-[#F4F0E6] text-gray-700 transition"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Answer & Evidence Display */}
      {response && (
        <div className="space-y-4">
          {/* Answer Card */}
          <div className="case-card p-5 rounded-lg border-l-4 border-l-[#C9962F] space-y-2">
            <div className="flex items-center justify-between pb-2 border-b border-gray-100">
              <div className="flex items-center space-x-2 text-xs font-bold font-serif uppercase tracking-wider text-[#131A2E]">
                <ShieldCheck className="w-4 h-4 text-[#C9962F]" />
                <span>Verified Evidence Synthesis</span>
              </div>
              <span className="text-[10px] text-gray-400 font-mono">
                Model: {response.model_used} {response.is_mock ? '(Mock Provider)' : ''}
              </span>
            </div>

            <p className="text-xs text-gray-800 leading-relaxed font-serif pt-1">
              {response.answer}
            </p>

            {response.uncertainty_note && (
              <div className="text-[11px] text-gray-500 italic pt-2 border-t border-gray-100">
                Notice: {response.uncertainty_note}
              </div>
            )}
          </div>

          {/* Supporting Evidence Chunks */}
          {response.evidence.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-700 font-mono">
                Direct Source Evidence ({response.evidence.length} passages retrieved)
              </h3>
              <div className="space-y-3">
                {response.evidence.map((ev, i) => (
                  <EvidenceCard key={ev.evidence_id || i} evidence={ev} rank={i + 1} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
