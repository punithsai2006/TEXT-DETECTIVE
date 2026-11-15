import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { AskQuestionResponse } from '../types';
import { EvidenceCard } from '../components/EvidenceCard';
import { HelpCircle, Send, Sparkles, AlertCircle, ShieldCheck, FileText, Cpu } from 'lucide-react';

export const AskQuestionPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<AskQuestionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getDynamicSuggestions = (): string[] => {
    const caseName = activeCase?.name?.toLowerCase() || '';
    if (caseName.includes('meridian')) {
      return [
        'Where was Alice Vance located between 10:00 PM and midnight?',
        'Did anyone enter Server Room B with a physical USB flash drive?',
        'What was discovered regarding the lock on the secure door?',
        'Who saw Bob Chen leave his keycard on the table?',
      ];
    }
    if (caseName.includes('blackwood')) {
      return [
        'Where was Julian Vance located during the vault alarm?',
        'Did the motion sensor alarm trigger in Zone 4?',
        'Who possesses keys to the basement vault safe?',
        'What vehicle was seen leaving near the greenhouse?',
      ];
    }
    if (caseName.includes('helios')) {
      return [
        'What temperature did Freezer Unit 4 maintain during August?',
        'Did the backup diesel generator engage during the storm?',
        'When was Batch HL-902B picked up by the CryoExpress courier?',
        'Were any adverse events reported for clinical trial patients?',
      ];
    }
    if (caseName.includes('apex')) {
      return [
        'Where was lead engineer Derek Cole between 19:45 and 21:30 UTC?',
        'Was custom firmware flashed to drone SkyHarrier-9?',
        'What payments or retainers were deposited into Derek Cole overseas account?',
        'Did the motor kill switch payload trigger at 250 meters?',
      ];
    }
    return [
      'What chronological timeline of events is documented for this incident?',
      'Which individuals, access credentials, or keycards were logged at the scene?',
      'What physical, digital, or sensor evidence was recovered in the case?',
      'Are there conflicting accounts between witness testimonies and system logs?',
    ];
  };

  const sampleQuestions = getDynamicSuggestions();

  const getSufficiencyBadge = (sufficiency?: string) => {
    switch (sufficiency) {
      case 'directly_established':
        return {
          label: 'Directly established',
          className: 'text-emerald-400 bg-emerald-950/80 border border-emerald-800/80',
        };
      case 'partially_established':
        return {
          label: 'Partially established',
          className: 'text-orange-400 bg-orange-950/80 border border-orange-800/80',
        };
      case 'multiple_events_found':
        return {
          label: 'Multiple events found',
          className: 'text-sky-400 bg-sky-950/80 border border-sky-800/80',
        };
      case 'insufficient_evidence':
        return {
          label: 'Insufficient evidence',
          className: 'text-rose-400 bg-rose-950/80 border border-rose-800/80',
        };
      default:
        return {
          label: 'Verified findings',
          className: 'text-slate-300 bg-slate-800 border border-slate-700',
        };
    }
  };

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
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
          Evidence-Grounded AI Assistant
        </div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
          Ask an Investigative Question
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          Queries verified evidence in case <strong>{activeCase?.name}</strong>. Strictly grounded in retrieved case chunks.
        </p>
      </div>

      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center shadow-sm">
          <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Question Form */}
      <div className="case-card p-5 sm:p-6 rounded-2xl space-y-4 shadow-sm border border-slate-200/80">
        <form onSubmit={handleAsk} className="flex flex-col sm:flex-row gap-2.5">
          <input
            type="text"
            required
            placeholder="Type your investigative question (e.g. keycard movements, timeline alibis, timestamps)..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="flex-1 p-3 text-xs sm:text-sm border border-slate-300 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none shadow-sm"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="px-5 py-3 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-xs font-semibold rounded-xl transition shadow-sm flex items-center justify-center space-x-1.5 disabled:opacity-50 shrink-0"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{loading ? 'Consulting Dossier...' : 'Ask Question'}</span>
          </button>
        </form>

        {/* Quick Question Chips */}
        <div className="flex items-center space-x-1.5 flex-wrap gap-1.5 text-[11px] text-slate-500 pt-1">
          <span className="font-semibold text-slate-700 flex items-center mr-1">
            <Sparkles className="w-3.5 h-3.5 text-blue-600 mr-1" /> Suggestions:
          </span>
          {sampleQuestions.map((q, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setQuestion(q)}
              className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 transition border border-slate-200/60"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Answer & Evidence Display */}
      {response && (() => {
        const badge = getSufficiencyBadge(response.evidence_sufficiency);
        return (
          <div className="space-y-5">
            {/* AI Investigation Answer Card */}
            <div className="bg-slate-950 text-slate-100 p-6 sm:p-7 rounded-2xl border border-slate-800 shadow-xl space-y-4">
              {/* Top row: Title & Pill badge */}
              <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-slate-800/80">
                <div className="flex items-center space-x-2 text-sm font-semibold text-slate-300">
                  <ShieldCheck className="w-4 h-4 text-blue-400" />
                  <span>AI Investigation Answer</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-0.5 rounded-full text-xs font-semibold ${badge.className}`}>
                    {badge.label}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono bg-slate-900 px-2.5 py-0.5 rounded-full border border-slate-800">
                    {response.model_used} {response.is_mock ? '(Offline Mode)' : ''}
                  </span>
                </div>
              </div>

              {/* Question as title */}
              <h2 className="text-lg sm:text-xl font-bold text-slate-100">
                {response.question}
              </h2>

              {/* Direct Answer */}
              <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">
                {response.direct_answer || response.answer}
              </p>

              {/* Supporting Evidence */}
              {response.supporting_evidence && response.supporting_evidence.length > 0 && (
                <div className="pt-2 space-y-3">
                  <h3 className="text-sm font-bold text-slate-200 tracking-wide">
                    Supporting evidence
                  </h3>
                  <div className="space-y-3">
                    {response.supporting_evidence.map((item, idx) => (
                      <div key={idx} className="bg-slate-900/90 border border-slate-800/90 rounded-xl p-3.5 space-y-1.5">
                        <div className="flex items-center gap-2 text-xs text-slate-300">
                          <span className="font-bold text-slate-300">Source:</span>
                          <code className="bg-slate-800 text-slate-200 px-2 py-0.5 rounded font-mono text-[11px] border border-slate-700">
                            {item.source}
                          </code>
                          {item.timestamp && (
                            <span className="text-slate-500 text-[11px] ml-auto font-mono">
                              {item.timestamp}
                            </span>
                          )}
                        </div>
                        <p className="text-xs sm:text-sm text-slate-300 italic pl-2.5 border-l-2 border-blue-500/70">
                          {item.quote}
                        </p>
                        {item.additional_detail && (
                          <p className="text-xs text-slate-400 pt-0.5">
                            <strong className="text-slate-300">Additional detail:</strong> {item.additional_detail}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Contradicting Evidence */}
              {response.contradicting_evidence && response.contradicting_evidence.length > 0 && (
                <div className="pt-2 space-y-3">
                  <h3 className="text-sm font-bold text-rose-300 tracking-wide flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 text-rose-400" />
                    <span>Contradicting evidence</span>
                  </h3>
                  <div className="space-y-3">
                    {response.contradicting_evidence.map((item, idx) => (
                      <div key={idx} className="bg-rose-950/30 border border-rose-900/60 rounded-xl p-3.5 space-y-1.5">
                        <div className="flex items-center gap-2 text-xs text-rose-200">
                          <span className="font-bold text-rose-300">Source:</span>
                          <code className="bg-rose-900/40 text-rose-200 px-2 py-0.5 rounded font-mono text-[11px] border border-rose-800/60">
                            {item.source}
                          </code>
                          {item.timestamp && (
                            <span className="text-rose-400/80 text-[11px] ml-auto font-mono">
                              {item.timestamp}
                            </span>
                          )}
                        </div>
                        <p className="text-xs sm:text-sm text-rose-200/90 italic pl-2.5 border-l-2 border-rose-500/80">
                          {item.quote}
                        </p>
                        {item.additional_detail && (
                          <p className="text-xs text-rose-300/80 pt-0.5">
                            <strong className="text-rose-200">Additional detail:</strong> {item.additional_detail}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Important Limitation */}
              {response.important_limitations && (
                <div className="pt-2 space-y-1.5">
                  <h3 className="text-sm font-bold text-slate-200 tracking-wide">
                    Important limitation
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    {response.important_limitations}
                  </p>
                </div>
              )}

              {/* Unresolved Questions */}
              {response.unresolved_questions && response.unresolved_questions.length > 0 && (
                <div className="pt-2 space-y-1.5">
                  <h3 className="text-sm font-bold text-slate-200 tracking-wide">
                    Unresolved questions
                  </h3>
                  <ul className="text-xs sm:text-sm text-slate-400 list-disc pl-5 space-y-1">
                    {response.unresolved_questions.map((uq, idx) => (
                      <li key={idx}>{uq}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Offline Mode Notice */}
              {response.is_mock && (
                <div className="text-[11px] text-slate-400 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 flex items-center gap-1.5 mt-2">
                  <Cpu className="w-3.5 h-3.5 shrink-0 text-blue-400" />
                  <span>Model: {response.model_used} (Offline Forensic Verification Mode). Grounded strictly in cross-referenced case files without external cloud hallucination.</span>
                </div>
              )}
            </div>

            {/* Supporting Evidence Chunks */}
            {response.evidence.length > 0 && (
              <div className="space-y-3 pt-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 px-1">
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
        );
      })()}
    </div>
  );
};
