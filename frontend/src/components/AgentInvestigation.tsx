import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { SourceCitation } from './SourceCitation';
import {
  Award,
  GitBranch,
  Clock,
  Scale,
  Gavel,
  Bot,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Play,
  FileText,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  Info,
  ChevronDown,
  ChevronRight,
  MessageSquare,
  Network,
  RotateCw,
  HelpCircle,
} from 'lucide-react';

type Finding = {
  finding_id: string;
  summary: string;
  finding_type: string;
  supporting_span_ids: string[];
  opposing_span_ids: string[];
  assumptions: string[];
  unresolved_questions: string[];
  verification_status: string;
  graph_paths: { node_ids: string[]; edges: { relation: string }[]; source_span_ids: string[] }[];
};

type Deliberation = {
  run_id: string;
  processing_status: string;
  stale: boolean;
  is_mock: boolean;
  model_name: string;
  model_provider: string;
  model_calls: number;
  tool_calls: number;
  warnings: string[];
  unresolved_questions: string[];
  agent_states: {
    name: string;
    responsibility: string;
    status: string;
    tool_calls: number;
    evidence_items: number;
    findings_produced: number;
    warnings: string[];
  }[];
  messages: {
    message_id: string;
    sender: string;
    tool_name: string;
    timestamp: string;
    decision_summary: string;
    evidence_span_ids: string[];
    success: boolean;
    error_message?: string;
  }[];
  graph_findings: Finding[];
  contradiction_findings: Finding[];
  supporting_arguments: Finding[];
  challenging_arguments: Finding[];
  neutral_assessment: Finding[];
  lead_summary: Finding[];
  timeline_milestones: {
    milestone_id: string;
    timestamp_range: string;
    summary: string;
    phase?: string;
    event_basis: string;
    uncertainty: boolean;
    source_span_ids: string[];
  }[];
};

const AGENT_METADATA: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string; bg: string }> = {
  LeadInvestigatorAgent: { icon: Award, color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200' },
  KnowledgeGraphRAGAgent: { icon: GitBranch, color: 'text-indigo-600', bg: 'bg-indigo-50 border-indigo-200' },
  ForensicTimelineAgent: { icon: Clock, color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200' },
  CrossExaminationAgent: { icon: Scale, color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200' },
  AdversarialHypothesisAgent: { icon: Gavel, color: 'text-rose-600', bg: 'bg-rose-50 border-rose-200' },
};

const PHASE_COLORS: Record<string, string> = {
  'Preparation': 'bg-purple-100 text-purple-800 border-purple-300',
  'Access or entry': 'bg-blue-100 text-blue-800 border-blue-300',
  'Critical incident': 'bg-rose-100 text-rose-800 border-rose-300',
  'Exit or aftermath': 'bg-amber-100 text-amber-800 border-amber-300',
  'Subsequent accounts and investigation': 'bg-slate-100 text-slate-800 border-slate-300',
};

const citationsList = (refs: string[]) => {
  const unique = Array.from(new Set(refs || []));
  if (!unique.length) return null;
  return (
    <div className="flex flex-wrap items-center gap-2 mt-2">
      <span className="text-[11px] font-semibold text-slate-400">Cited Sources:</span>
      {unique.map((s, i) => (
        <SourceCitation key={s} spanId={s} label={`Source ${i + 1}`} />
      ))}
    </div>
  );
};

const renderFindings = (items: Finding[], emptyMessage: string = 'No verified findings recorded.') => {
  if (!items || items.length === 0) {
    return <p className="text-xs text-slate-400 italic py-2">{emptyMessage}</p>;
  }
  return (
    <div className="space-y-3">
      {items.map((f) => (
        <article key={f.finding_id} className="case-card p-4 rounded-xl border border-slate-200/90 shadow-sm space-y-2">
          <p className="text-sm font-medium text-slate-800 leading-relaxed">{f.summary}</p>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="px-2 py-0.5 rounded font-mono font-semibold bg-slate-100 text-slate-700">
              {f.finding_type}
            </span>
            <span className="text-slate-400">·</span>
            <span className="text-slate-500 font-mono text-[11px]">{f.verification_status}</span>
          </div>
          {citationsList([...(f.supporting_span_ids || []), ...(f.opposing_span_ids || [])])}
          {f.assumptions && f.assumptions.length > 0 && (
            <p className="text-xs text-amber-700 bg-amber-50/60 p-2 rounded border border-amber-100">
              <strong>Assumptions:</strong> {f.assumptions.join('; ')}
            </p>
          )}
          {f.unresolved_questions && f.unresolved_questions.length > 0 && (
            <p className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-200">
              <strong>Unresolved Leads:</strong> {f.unresolved_questions.join('; ')}
            </p>
          )}
          {f.graph_paths && f.graph_paths.length > 0 && (
            <details className="text-xs border-t border-slate-100 pt-2 mt-2">
              <summary className="cursor-pointer font-semibold text-blue-600 hover:text-blue-800">
                Inspect {f.graph_paths.length} Graph Relational Path(s)
              </summary>
              <div className="space-y-2 mt-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                {f.graph_paths.map((p, i) => (
                  <div key={i} className="py-1 text-[11px] font-mono break-all border-b border-slate-100 last:border-0">
                    <p className="text-slate-900 font-bold">{p.node_ids.join(' ➔ ')}</p>
                    <p className="text-slate-500">{p.edges.map((e) => e.relation).join(' ➔ ')}</p>
                    {citationsList(p.source_span_ids)}
                  </div>
                ))}
              </div>
            </details>
          )}
        </article>
      ))}
    </div>
  );
};

export const AgentInvestigation: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [data, setData] = useState<Deliberation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState('');
  const [provider, setProvider] = useState<{ status: string; model: string; is_mock: boolean } | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'debate' | 'graph' | 'timeline' | 'actions'>('overview');

  const endpoint = `/api/cases/${activeCaseId}`;

  const load = async () => {
    if (!activeCaseId) return;
    const response = await fetch(`${endpoint}/agents/deliberation`);
    const value = await response.json();
    if (!response.ok) throw new Error(value.detail || 'Unable to load agent activity');
    setData(value?.schema_version === 'five-agent-evidence-v1' ? value : null);
  };

  useEffect(() => {
    if (!activeCaseId) return;
    load().catch((e) => setError(e.message));
    fetch('/api/provider/readiness')
      .then((r) => r.json())
      .then(setProvider)
      .catch(() => {});
  }, [activeCaseId]);

  useEffect(() => {
    if (!busy || !activeCaseId) return;
    const timer = window.setInterval(() => {
      load().catch(() => {});
      api
        .getAnalysisStatus(activeCaseId)
        .then((s) => setProgress(`${s.current_module}: ${s.message}`))
        .catch(() => {});
    }, 1500);
    return () => window.clearInterval(timer);
  }, [busy, activeCaseId]);

  const run = async (pipeline = false, force = false) => {
    if (!activeCaseId) return;
    setBusy(true);
    setError('');
    setProgress('Engaging five-agent collaborative investigation…');
    try {
      if (pipeline) {
        await api.runAnalysis(activeCaseId);
      } else {
        const response = await fetch(`${endpoint}/agents/run?force=${force}`, { method: 'POST' });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || 'Agent investigation failed');
        setData(result);
        if (result.processing_status !== 'completed') throw new Error(result.warnings.join('; '));
      }
      await load();
      setProgress('Multi-agent deliberation completed. Verified findings published.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Investigation failed');
      await load().catch(() => {});
    } finally {
      setBusy(false);
    }
  };

  if (!activeCaseId) {
    return (
      <div className="case-card p-12 text-center rounded-2xl">
        <Bot className="w-10 h-10 text-slate-300 mx-auto mb-2" />
        <h3 className="text-base font-bold text-slate-800">No Active Investigation Selected</h3>
        <p className="text-xs text-slate-500 mt-1">Please select an investigation from the header or case directory.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto" aria-busy={busy}>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs uppercase font-bold tracking-wider text-blue-600">
            <Bot className="w-4 h-4 text-blue-600" />
            <span>Autonomous Multi-Agent System (MAS)</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
            Five-Agent Collaborative Deliberation
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Investigation: <strong>{activeCase?.name}</strong> • Bounded execution across 5 specialized roles.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center rounded-lg border border-slate-300 overflow-hidden bg-white shadow-sm p-0.5 text-xs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 font-semibold rounded-md transition ${
              activeTab === 'overview' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Agent Overview
          </button>
          <button
            onClick={() => setActiveTab('debate')}
            className={`px-3 py-1.5 font-semibold rounded-md transition ${
              activeTab === 'debate' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Adversarial Debate
          </button>
          <button
            onClick={() => setActiveTab('graph')}
            className={`px-3 py-1.5 font-semibold rounded-md transition ${
              activeTab === 'graph' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Graph-RAG
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-3 py-1.5 font-semibold rounded-md transition ${
              activeTab === 'timeline' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Forensic Milestones
          </button>
          <button
            onClick={() => setActiveTab('actions')}
            className={`px-3 py-1.5 font-semibold rounded-md transition ${
              activeTab === 'actions' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Action Logs ({data?.messages?.length || 0})
          </button>
        </div>
      </div>

      {/* Model Provider Info Banner */}
      {provider && (
        <div className="p-3 bg-slate-100 rounded-xl border border-slate-200 text-xs flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-blue-600" />
            <span>
              <strong>Active Model:</strong> {provider.model || 'Not configured'} ({provider.status})
            </span>
          </div>
          {provider.is_mock && (
            <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[10px] uppercase tracking-wider border border-amber-300">
              Offline Demonstration Mode (Fixture Scripted)
            </span>
          )}
        </div>
      )}

      {/* Action Controls Toolbar */}
      <div className="flex flex-wrap items-center gap-2.5">
        <button
          disabled={busy}
          onClick={() => run(true)}
          className="flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-50"
        >
          <Play className="w-3.5 h-3.5" />
          <span>Run Full Investigation</span>
        </button>
        <button
          disabled={busy}
          onClick={() => run(false, true)}
          className="flex items-center space-x-1.5 px-3.5 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-50"
        >
          <RotateCw className="w-3.5 h-3.5 text-slate-500" />
          <span>Rerun Deliberation</span>
        </button>
        <button
          disabled={busy}
          onClick={() => run()}
          className="flex items-center space-x-1.5 px-3.5 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-50"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
          <span>Retry Unfinished Stages</span>
        </button>
        <button
          onClick={() => load().catch((e) => setError(e.message))}
          className="flex items-center space-x-1.5 px-3.5 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-sm transition"
        >
          <span>Refresh Partial Results</span>
        </button>
        <div className="ml-auto flex items-center gap-2">
          <Link
            to="/evidence"
            className="flex items-center space-x-1 px-3 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-sm transition"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>View Evidence</span>
          </Link>
          <Link
            to="/report"
            className="flex items-center space-x-1 px-3 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition"
          >
            <span>Dossier Report</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Progress / Status Announcement */}
      {progress && (
        <p role="status" aria-live="polite" className="text-xs font-mono text-blue-700 bg-blue-50/70 p-2.5 rounded-lg border border-blue-200">
          {progress}
        </p>
      )}
      {error && (
        <p role="alert" className="text-xs font-mono text-rose-700 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
          {error}
        </p>
      )}

      {!data ? (
        <div className="case-card p-12 text-center rounded-2xl">
          <Bot className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Multi-Agent Deliberation Recorded</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            Click <strong>Run Full Investigation</strong> to ingest documents, perform RAG & graph traversals,
            cross-examine claims, and initiate the 5-agent deliberation.
          </p>
        </div>
      ) : (
        <>
          {/* Executive Deliberation Status Header */}
          <div className="case-card p-4 rounded-xl border border-slate-200/90 shadow-sm flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-slate-50 to-white">
            <div className="flex items-center space-x-3">
              <span
                className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                  data.processing_status === 'completed'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : 'bg-amber-100 text-amber-800 border border-amber-300'
                }`}
              >
                {data.processing_status}
              </span>
              <span className="text-xs font-semibold text-slate-700">
                {data.is_mock ? 'Scripted Fixture Mode' : 'Live LLM Inference'}
              </span>
              <span className="text-slate-300">|</span>
              <span className="text-xs text-slate-500 font-mono">
                {data.model_calls} LLM calls · {data.tool_calls} stage tool executions
              </span>
            </div>
            {data.stale && (
              <span className="text-xs text-rose-700 font-bold bg-rose-50 px-2.5 py-1 rounded border border-rose-200">
                Sources Changed — Stale Run
              </span>
            )}
          </div>

          {data.warnings && data.warnings.length > 0 && (
            <div className="space-y-1">
              {data.warnings.map((w, i) => (
                <p key={i} role="alert" className="text-xs text-amber-800 bg-amber-50 p-2.5 rounded-lg border border-amber-200 flex items-center space-x-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>{w}</span>
                </p>
              ))}
            </div>
          )}

          {/* TAB 1: OVERVIEW & 5 AGENTS */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* 5 Specialized Agent Cards */}
              <section aria-label="Agent status overview">
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-600 mb-3">Specialized Agent Roster</h2>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {data.agent_states.map((a) => {
                    const meta = AGENT_METADATA[a.name] || { icon: Bot, color: 'text-slate-600', bg: 'bg-slate-50 border-slate-200' };
                    const Icon = meta.icon;
                    return (
                      <article key={a.name} className="case-card p-4 rounded-xl border border-slate-200 shadow-sm space-y-2 flex flex-col justify-between">
                        <div>
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center space-x-2">
                              <div className={`p-1.5 rounded-lg ${meta.bg}`}>
                                <Icon className={`w-4 h-4 ${meta.color}`} />
                              </div>
                              <h3 className="font-bold text-xs text-slate-900 truncate" title={a.name}>
                                {a.name}
                              </h3>
                            </div>
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                                a.status === 'completed'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : a.status === 'running'
                                  ? 'bg-blue-100 text-blue-800 animate-pulse'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {a.status}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-2 leading-relaxed">{a.responsibility}</p>
                        </div>
                        <div className="border-t border-slate-100 pt-2 text-[11px] text-slate-400 font-mono flex items-center justify-between">
                          <span>{a.tool_calls} tool calls</span>
                          <span>{a.evidence_items} cited items</span>
                          <span>{a.findings_produced} outputs</span>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </section>

              {/* Lead Investigator Synthesized Evidence Summary */}
              <section className="case-card p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center space-x-2">
                  <Award className="w-5 h-5 text-blue-600" />
                  <h2 className="text-base font-bold text-slate-900">Lead Investigator Evidence Assessment</h2>
                </div>
                <p className="text-xs text-slate-500">
                  Evidence-grounded executive summary synthesized by LeadInvestigatorAgent from verified source citations.
                </p>
                {renderFindings(data.lead_summary, 'No executive summary produced yet.')}
              </section>

              {/* Contextual Contradiction Findings */}
              <section className="case-card p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Scale className="w-5 h-5 text-amber-600" />
                    <h2 className="text-base font-bold text-slate-900">Cross-Examination Contradiction Findings</h2>
                  </div>
                  <Link to="/contradictions" className="text-xs font-semibold text-blue-600 hover:underline">
                    View Full Contradictions Engine ➔
                  </Link>
                </div>
                {renderFindings(data.contradiction_findings, 'No contradictory pairs classified.')}
              </section>

              {/* Unresolved Questions */}
              <section className="case-card p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center space-x-2">
                  <HelpCircle className="w-5 h-5 text-purple-600" />
                  <h2 className="text-base font-bold text-slate-900">Remaining Unresolved Investigation Questions</h2>
                </div>
                {data.unresolved_questions && data.unresolved_questions.length > 0 ? (
                  <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-700">
                    {data.unresolved_questions.map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-400 italic">No remaining unresolved questions.</p>
                )}
              </section>
            </div>
          )}

          {/* TAB 2: ADVERSARIAL DEBATE ARENA */}
          {activeTab === 'debate' && (
            <div className="space-y-6">
              <div className="case-card p-4 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-600">
                <strong>Adversarial Hypothesis Evaluation Arena:</strong> Three bounded debate roles assess competing interpretations.
                Supporting Advocate argues evidentiary support; Challenging Advocate presents ambiguities, contrary passages, and alternatives;
                Neutral Evidence Arbiter summarizes supported vs disputed claims without rendering a legal verdict.
              </div>

              {/* Supporting Advocate */}
              <section className="case-card p-5 rounded-2xl border-l-4 border-l-blue-600 border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-5 h-5 text-blue-600" />
                  <h2 className="text-base font-bold text-slate-900">Supporting Advocate</h2>
                </div>
                <p className="text-xs text-slate-500">Presents evidence-supported arguments grounded strictly in cited source passages.</p>
                {renderFindings(data.supporting_arguments, 'No supporting arguments published.')}
              </section>

              {/* Challenging Advocate */}
              <section className="case-card p-5 rounded-2xl border-l-4 border-l-rose-600 border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center space-x-2">
                  <ShieldAlert className="w-5 h-5 text-rose-600" />
                  <h2 className="text-base font-bold text-slate-900">Challenging Advocate</h2>
                </div>
                <p className="text-xs text-slate-500">Identifies contrary evidence, alternative explanations, and unverified assumptions.</p>
                {renderFindings(data.challenging_arguments, 'No challenging arguments published.')}
              </section>

              {/* Neutral Evidence Arbiter */}
              <section className="case-card p-5 rounded-2xl border-l-4 border-l-purple-600 border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center space-x-2">
                  <Gavel className="w-5 h-5 text-purple-600" />
                  <h2 className="text-base font-bold text-slate-900">Neutral Evidence Arbiter</h2>
                </div>
                <p className="text-xs text-slate-500">Distinguishes supported, disputed, and unresolved assertions without a legal verdict.</p>
                {renderFindings(data.neutral_assessment, 'No neutral assessment recorded.')}
              </section>

              <div className="text-right">
                <Link to="/hypotheses" className="text-xs font-semibold text-blue-600 hover:underline">
                  Inspect Unchanged Deterministic Mathematical Scores ➔
                </Link>
              </div>
            </div>
          )}

          {/* TAB 3: GRAPH-RAG */}
          {activeTab === 'graph' && (
            <div className="space-y-6">
              <section className="case-card p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <GitBranch className="w-5 h-5 text-indigo-600" />
                    <h2 className="text-base font-bold text-slate-900">KnowledgeGraphRAGAgent Neighborhood Traversals</h2>
                  </div>
                  <Link to="/graph" className="text-xs font-semibold text-blue-600 hover:underline">
                    Open Interactive Case Graph ➔
                  </Link>
                </div>
                <p className="text-xs text-slate-500">
                  Explores connected multi-hop paths between people, locations, objects, and claims.
                  Graph paths are leads, not independent corroboration.
                </p>
                {renderFindings(data.graph_findings, 'No graph findings recorded.')}
              </section>
            </div>
          )}

          {/* TAB 4: SUMMARY TIMELINE */}
          {activeTab === 'timeline' && (
            <div className="space-y-6">
              <section className="case-card p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-emerald-600" />
                    <h2 className="text-base font-bold text-slate-900">Forensic Summary Timeline</h2>
                  </div>
                  <Link to="/timeline" className="text-xs font-semibold text-blue-600 hover:underline">
                    View Complete Detailed Timeline ➔
                  </Link>
                </div>
                <p className="text-xs text-slate-500">
                  Synthesized milestones categorized by basis (observed, reported, logged, inferred) and optional investigation phases.
                </p>

                {data.timeline_milestones && data.timeline_milestones.length > 0 ? (
                  <div className="space-y-3 relative border-l-2 border-slate-200 pl-4 ml-2">
                    {data.timeline_milestones.map((m) => (
                      <article key={m.milestone_id} className="relative space-y-1.5 pb-4">
                        <div className="absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full bg-blue-600 border-2 border-white" />
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-900">{m.timestamp_range}</span>
                          {m.phase && (
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${PHASE_COLORS[m.phase] || 'bg-slate-100 text-slate-700'}`}>
                              {m.phase}
                            </span>
                          )}
                          <span className="text-[11px] font-mono text-slate-500">
                            Basis: <strong>{m.event_basis}</strong>
                          </span>
                          {m.uncertainty && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-100 text-amber-800 font-semibold">
                              Uncertain Timestamp
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed">{m.summary}</p>
                        {citationsList(m.source_span_ids)}
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No summary milestones synthesized.</p>
                )}
              </section>
            </div>
          )}

          {/* TAB 5: ACTION LOGS & TRANSCRIPTS */}
          {activeTab === 'actions' && (
            <div className="space-y-4">
              <div className="case-card p-4 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-600">
                <strong>Observable Agent Deliberation Transcript:</strong> Displays chronological tool calls, delegations,
                and verification results. Hidden model reasoning is excluded to protect judicial transparency.
              </div>

              <div className="space-y-2.5">
                {data.messages && data.messages.length > 0 ? (
                  data.messages.map((m) => (
                    <details key={m.message_id} className="case-card p-3 rounded-xl border border-slate-200 shadow-sm text-xs space-y-2">
                      <summary className="cursor-pointer flex items-center justify-between font-semibold text-slate-800">
                        <div className="flex items-center space-x-2">
                          <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-mono text-[10px] font-bold">
                            {m.sender}
                          </span>
                          <span className="text-slate-400">➔</span>
                          <span className="text-slate-700 font-mono">{m.tool_name || 'action'}</span>
                        </div>
                        <div className="flex items-center space-x-2 text-[11px]">
                          <span className={m.success ? 'text-emerald-600 font-bold' : 'text-rose-600 font-bold'}>
                            {m.success ? 'Success' : 'Failed'}
                          </span>
                          <time className="text-slate-400 font-mono">{new Date(m.timestamp).toLocaleTimeString()}</time>
                        </div>
                      </summary>
                      <div className="pt-2 border-t border-slate-100 space-y-1.5">
                        <p className="text-slate-800 leading-relaxed">{m.decision_summary}</p>
                        {m.error_message && (
                          <p role="alert" className="text-rose-700 bg-rose-50 p-2 rounded border border-rose-200">
                            <strong>Error:</strong> {m.error_message}
                          </p>
                        )}
                        {citationsList(m.evidence_span_ids)}
                      </div>
                    </details>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 italic">No agent communication messages recorded.</p>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
