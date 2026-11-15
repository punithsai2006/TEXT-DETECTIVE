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
    if (caseName.includes('lakeview')) {
      return [
        'Where was archivist Tom Reyes between 7:30 PM and 10:30 PM?',
        'Who swiped Keycard 104 at the Rare Manuscript Vault Door at 20:45?',
        'Did the vault temperature sensor trigger a climate excursion alert?',
        'Was an overseas wire transfer made to Tom Reyes by Ronald Vane?',
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
      {response && (
        <div className="space-y-4">
          {/* Answer Card */}
          <div className="case-card p-5 sm:p-6 rounded-2xl border-l-4 border-l-blue-600 space-y-3 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-900">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                <span>Verified Evidence Synthesis</span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200">
                Model: {response.model_used} {response.is_mock ? '(Mock Offline)' : ''}
              </span>
            </div>

            <p className="text-xs sm:text-sm text-slate-800 leading-relaxed pt-1 whitespace-pre-line">
              {response.answer}
            </p>

            {response.is_mock && (
              <div className="text-[11px] text-blue-700 bg-blue-50/80 p-2.5 rounded-lg border border-blue-200/60 flex items-center gap-1.5 mt-2">
                <Cpu className="w-3.5 h-3.5 shrink-0 text-blue-600" />
                <span>Offline Mock Mode: Answer synthesized directly from retrieved passages without live API call.</span>
              </div>
            )}

            {response.uncertainty_note && (
              <div className="text-[11px] text-amber-700 bg-amber-50 p-2.5 rounded-lg border border-amber-200/60 flex items-center gap-1.5 mt-2">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Notice: {response.uncertainty_note}</span>
              </div>
            )}
          </div>

          {/* Supporting Evidence Chunks */}
          {response.evidence.length > 0 && (
            <div className="space-y-3">
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
      )}
    </div>
  );
};
