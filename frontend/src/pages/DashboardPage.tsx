import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import {
  FolderArchive,
  FileText,
  Users,
  Clock,
  AlertTriangle,
  BrainCircuit,
  ArrowRight,
  Play,
  FileCheck2,
  PlusCircle,
  Sparkles,
  ShieldCheck,
  Search,
  Scale,
  Network,
  CheckCircle2,
  RotateCw,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { cases, activeCase, activeCaseId, setActiveCaseId, refreshCases } = useCase();
  const navigate = useNavigate();
  const [analyzing, setAnalyzing] = useState(false);

  // Aggregate stats from stored cases
  const totalCases = cases.length;
  const totalDocs = cases.reduce((sum, c) => sum + (c.document_count || 0), 0);
  const totalEntities = cases.reduce((sum, c) => sum + (c.entity_count || 0), 0);
  const totalEvents = cases.reduce((sum, c) => sum + (c.event_count || 0), 0);
  const totalContradictions = cases.reduce((sum, c) => sum + (c.contradiction_count || 0), 0);
  const totalHypotheses = cases.reduce((sum, c) => sum + (c.hypothesis_count || 0), 0);

  const stats = [
    { label: 'Total Investigations', value: totalCases, icon: FolderArchive, color: 'text-blue-600', bg: 'bg-blue-50 border-blue-100' },
    { label: 'Documents Processed', value: totalDocs, icon: FileText, color: 'text-indigo-600', bg: 'bg-indigo-50 border-indigo-100' },
    { label: 'Entities Extracted', value: totalEntities, icon: Users, color: 'text-amber-600', bg: 'bg-amber-50 border-amber-100' },
    { label: 'Timeline Events', value: totalEvents, icon: Clock, color: 'text-teal-600', bg: 'bg-teal-50 border-teal-100' },
    { label: 'Discrepancies Flagged', value: totalContradictions, icon: AlertTriangle, color: 'text-rose-600', bg: 'bg-rose-50 border-rose-100' },
    { label: 'Hypotheses Evaluated', value: totalHypotheses, icon: BrainCircuit, color: 'text-purple-600', bg: 'bg-purple-50 border-purple-100' },
  ];

  const handleRunFullAnalysis = async () => {
    if (!activeCaseId) return;
    setAnalyzing(true);
    try {
      await api.runAnalysis(activeCaseId);
      await refreshCases();
      navigate('/report');
    } catch (e: any) {
      alert(`Analysis run failed: ${e.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const modules = [
    { num: '01', title: 'Document Ingestion', desc: `${activeCase?.document_count || 0} Docs Loaded`, link: '/documents', icon: FileText, done: (activeCase?.document_count || 0) > 0 },
    { num: '02', title: 'Timeline Sequence', desc: `${activeCase?.event_count || 0} Events Ordered`, link: '/timeline', icon: Clock, done: (activeCase?.event_count || 0) > 0 },
    { num: '03', title: 'Hybrid RAG Index', desc: 'Dense + BM25 Vector', link: '/evidence', icon: Search, done: (activeCase?.document_count || 0) > 0 },
    { num: '04', title: 'Contradiction Engine', desc: `${activeCase?.contradiction_count || 0} Conflicts Found`, link: '/contradictions', icon: Scale, done: (activeCase?.contradiction_count || 0) > 0 },
    { num: '05', title: 'Hypothesis Scorer', desc: `${activeCase?.hypothesis_count || 0} Theories Ranked`, link: '/hypotheses', icon: BrainCircuit, done: (activeCase?.hypothesis_count || 0) > 0 },
    { num: '06', title: 'Investigation Dossier', desc: 'Traceable Audit Report', link: '/report', icon: FileCheck2, done: activeCase?.status === 'completed' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Welcome / Hero Banner */}
      <div className="bg-slate-900 text-white p-6 sm:p-7 rounded-2xl border border-slate-800 shadow-sm relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-blue-600/10 to-transparent pointer-events-none hidden md:block" />
        <div className="relative z-10 max-w-3xl">
          <div className="flex items-center space-x-2 text-xs font-semibold tracking-wider text-blue-400 uppercase">
            <Sparkles className="w-4 h-4" />
            <span>Agentic Text Analytics Framework</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mt-1.5">
            Evidence-Based Investigation Cockpit
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
            Multi-document reasoning architecture designed for complex incident investigations.
            Extracts facts, reconstructs chronological timelines, flags cross-document discrepancies,
            ranks candidate explanations via evidence-based scoring, and produces fully traceable dossiers.
          </p>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              onClick={() => navigate('/new')}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-xs font-semibold transition-all shadow-sm"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Start New Investigation</span>
            </button>
            {activeCaseId && (
              <button
                onClick={handleRunFullAnalysis}
                disabled={analyzing}
                className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white text-xs font-semibold transition-all shadow-sm disabled:opacity-50"
              >
                <RotateCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
                <span>{analyzing ? 'Executing Pipeline...' : 'Run Full Pipeline'}</span>
              </button>
            )}
            <button
              onClick={() => navigate('/report')}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition"
            >
              <FileCheck2 className="w-4 h-4 text-blue-400" />
              <span>Audit Dossier</span>
            </button>
          </div>
        </div>
      </div>

      {/* 6-Module Architecture Visualizer */}
      <div className="space-y-2">
        <div className="flex items-center justify-between px-1">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <span>Investigation Pipeline & Analytics Modules</span>
          </div>
          <span className="text-xs text-slate-400">Click any module to inspect</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {modules.map((m) => {
            const Icon = m.icon;
            return (
              <div
                key={m.num}
                onClick={() => navigate(m.link)}
                className="case-card p-3 rounded-xl cursor-pointer hover:border-blue-400 transition-all flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                      {m.num}
                    </span>
                    {m.done ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-slate-200" />
                    )}
                  </div>
                  <h4 className="font-semibold text-xs text-slate-800 mt-2 group-hover:text-blue-600 transition-colors">
                    {m.title}
                  </h4>
                </div>
                <div className="text-[11px] text-slate-500 mt-2 truncate font-medium">
                  {m.desc}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Aggregate Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} className="case-card p-3.5 rounded-xl flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium text-slate-500 leading-snug">{s.label}</span>
                <div className={`p-1.5 rounded-lg border ${s.bg}`}>
                  <Icon className={`w-3.5 h-3.5 ${s.color}`} />
                </div>
              </div>
              <div className="text-2xl font-bold font-mono text-slate-900 mt-2">
                {s.value}
              </div>
            </div>
          );
        })}
      </div>

      {/* Active Case Summary Spotlight Card */}
      {activeCase ? (
        <div className="case-card p-5 sm:p-6 rounded-2xl border-l-4 border-l-blue-600 shadow-sm">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200">
                  Active Case
                </span>
                {activeCase.is_demo && (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200">
                    Benchmark Case
                  </span>
                )}
                <span className="text-xs font-mono text-slate-400">ID: {activeCase.case_id}</span>
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 mt-2">
                {activeCase.name}
              </h2>
              <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-3xl leading-relaxed">
                {activeCase.description || 'No description provided.'}
              </p>
            </div>

            <div className="flex items-center flex-wrap gap-2">
              <button
                onClick={() => navigate('/timeline')}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-900 hover:bg-slate-800 text-white transition flex items-center shadow-sm"
              >
                <span>Timeline</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
              </button>
              <button
                onClick={() => navigate('/contradictions')}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-500 text-white transition flex items-center shadow-sm"
              >
                <span>Contradictions</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
              </button>
              <button
                onClick={() => navigate('/hypotheses')}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center shadow-sm"
              >
                <span>Hypotheses</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
              </button>
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
              <span className="text-slate-500 text-[11px] font-medium">Evidence Files</span>
              <div className="text-lg font-bold text-slate-900 font-mono mt-0.5">
                {activeCase.document_count} files
              </div>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
              <span className="text-slate-500 text-[11px] font-medium">Sequenced Events</span>
              <div className="text-lg font-bold text-slate-900 font-mono mt-0.5">
                {activeCase.event_count} events
              </div>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
              <span className="text-slate-500 text-[11px] font-medium">Cross-Doc Conflicts</span>
              <div className="text-lg font-bold text-rose-600 font-mono mt-0.5">
                {activeCase.contradiction_count} flagged
              </div>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
              <span className="text-slate-500 text-[11px] font-medium">Ranked Explanations</span>
              <div className="text-lg font-bold text-purple-700 font-mono mt-0.5">
                {activeCase.hypothesis_count} scored
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="case-card p-10 rounded-2xl text-center">
          <FolderArchive className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Active Case Selected</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Choose an existing case from the directory or create a new investigation to begin.
          </p>
          <button
            onClick={() => navigate('/cases')}
            className="mt-4 px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition shadow-sm"
          >
            Open Cases Directory
          </button>
        </div>
      )}

      {/* Investigations Directory Preview */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Case Files Repository ({cases.length})
          </h3>
          <button
            onClick={() => navigate('/cases')}
            className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
          >
            <span>Manage Directory</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {cases.map((c) => {
            const isActive = c.case_id === activeCase?.case_id;
            return (
              <div
                key={c.case_id}
                onClick={() => setActiveCaseId(c.case_id)}
                className={`case-card p-4 rounded-xl cursor-pointer transition-all ${
                  isActive
                    ? 'ring-2 ring-blue-600 border-blue-300 bg-blue-50/20'
                    : 'hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                      c.is_demo
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : 'bg-slate-100 text-slate-700 border border-slate-200'
                    }`}
                  >
                    {c.is_demo ? 'BENCHMARK' : 'USER'}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(c.created_at).toLocaleDateString()}
                  </span>
                </div>

                <h4 className="font-bold text-sm text-slate-900 mt-2 truncate">
                  {c.name}
                </h4>
                <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                  {c.description || 'No description provided.'}
                </p>

                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>{c.document_count} docs • {c.contradiction_count} conflicts</span>
                  <span className={`font-semibold ${isActive ? 'text-blue-600' : 'text-slate-400'}`}>
                    {isActive ? 'ACTIVE' : 'SELECT'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
