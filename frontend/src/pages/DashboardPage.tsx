import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCase } from '../context/CaseContext';
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
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { cases, activeCase, setActiveCaseId } = useCase();
  const navigate = useNavigate();

  // Aggregate stats from stored cases
  const totalCases = cases.length;
  const totalDocs = cases.reduce((sum, c) => sum + (c.document_count || 0), 0);
  const totalEntities = cases.reduce((sum, c) => sum + (c.entity_count || 0), 0);
  const totalEvents = cases.reduce((sum, c) => sum + (c.event_count || 0), 0);
  const totalContradictions = cases.reduce((sum, c) => sum + (c.contradiction_count || 0), 0);
  const totalHypotheses = cases.reduce((sum, c) => sum + (c.hypothesis_count || 0), 0);

  const stats = [
    { label: 'Investigations', value: totalCases, icon: FolderArchive, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Documents Processed', value: totalDocs, icon: FileText, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Entities Extracted', value: totalEntities, icon: Users, color: 'text-amber-600', bg: 'bg-amber-50' },
    { label: 'Timeline Events', value: totalEvents, icon: Clock, color: 'text-teal-600', bg: 'bg-teal-50' },
    { label: 'Contradictions Detected', value: totalContradictions, icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50' },
    { label: 'Hypotheses Ranked', value: totalHypotheses, icon: BrainCircuit, color: 'text-purple-600', bg: 'bg-purple-50' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-[#131A2E] text-white p-6 rounded-xl border border-[#2A344E] shadow-sm relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="flex items-center space-x-2 text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Agentic Investigation Cockpit</span>
          </div>
          <h1 className="text-2xl font-bold font-serif text-[#F4F0E6] mt-1">
            Text Detective Analytics Framework
          </h1>
          <p className="text-xs text-[#B0BBD8] mt-2 leading-relaxed">
            Multi-document reasoning pipeline for incident reports, witness interviews, badge logs, and emails.
            Extracts facts, detects cross-document contradictions, ranks candidate explanations using evidence,
            and produces source-traceable reports.
          </p>

          <div className="mt-4 flex items-center space-x-3">
            <button
              onClick={() => navigate('/new')}
              className="flex items-center space-x-1.5 px-4 py-2 rounded bg-[#C9962F] text-[#131A2E] text-xs font-bold hover:bg-[#E0B354] transition shadow"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Start New Investigation</span>
            </button>
            <button
              onClick={() => navigate('/report')}
              className="flex items-center space-x-1.5 px-3 py-2 rounded bg-[#1D2744] text-[#E0B354] border border-[#313E61] text-xs font-medium hover:bg-[#253255] transition"
            >
              <FileCheck2 className="w-4 h-4" />
              <span>View Dossier Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* Aggregate Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} className="case-card p-3 rounded-lg flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium text-gray-500 leading-tight">{s.label}</span>
                <div className={`p-1.5 rounded ${s.bg}`}>
                  <Icon className={`w-3.5 h-3.5 ${s.color}`} />
                </div>
              </div>
              <div className="text-xl font-bold font-mono text-[#131A2E] mt-2">
                {s.value}
              </div>
            </div>
          );
        })}
      </div>

      {/* Active Case Summary Hero Card */}
      {activeCase ? (
        <div className="case-card p-5 rounded-lg border-2 border-[#C9962F]">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center space-x-2">
                <span className="stamp-label stamp-gold text-[10px]">Active Investigation</span>
                {activeCase.is_demo && (
                  <span className="stamp-label stamp-navy text-[10px]">Demo Benchmark</span>
                )}
                <span className="text-xs uppercase font-mono text-gray-400">ID: {activeCase.case_id}</span>
              </div>
              <h2 className="text-lg font-bold font-serif text-[#131A2E] mt-1.5">
                {activeCase.name}
              </h2>
              <p className="text-xs text-gray-600 mt-1 max-w-2xl">
                {activeCase.description || 'No description provided.'}
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => navigate('/timeline')}
                className="px-3 py-1.5 text-xs font-medium rounded bg-[#131A2E] text-white hover:bg-[#1D2744] transition flex items-center"
              >
                <span>Timeline</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </button>
              <button
                onClick={() => navigate('/contradictions')}
                className="px-3 py-1.5 text-xs font-medium rounded bg-red-600 text-white hover:bg-red-700 transition flex items-center"
              >
                <span>Contradictions</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </button>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-[#FAF8F3] p-2.5 rounded">
              <span className="text-gray-500 text-[11px]">Documents</span>
              <div className="text-base font-bold text-[#131A2E] font-mono mt-0.5">
                {activeCase.document_count} files
              </div>
            </div>
            <div className="bg-[#FAF8F3] p-2.5 rounded">
              <span className="text-gray-500 text-[11px]">Timeline Events</span>
              <div className="text-base font-bold text-[#131A2E] font-mono mt-0.5">
                {activeCase.event_count} events
              </div>
            </div>
            <div className="bg-[#FAF8F3] p-2.5 rounded">
              <span className="text-gray-500 text-[11px]">Planted Conflicts</span>
              <div className="text-base font-bold text-red-600 font-mono mt-0.5">
                {activeCase.contradiction_count} flagged
              </div>
            </div>
            <div className="bg-[#FAF8F3] p-2.5 rounded">
              <span className="text-gray-500 text-[11px]">Hypotheses</span>
              <div className="text-base font-bold text-purple-700 font-mono mt-0.5">
                {activeCase.hypothesis_count} scored
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="case-card p-8 rounded-lg text-center">
          <FolderArchive className="w-10 h-10 text-gray-400 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-gray-700">No Active Case Selected</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            Choose an existing case from the directory or create a new investigation to begin.
          </p>
          <button
            onClick={() => navigate('/cases')}
            className="mt-3 px-3 py-1.5 text-xs font-semibold rounded bg-[#C9962F] text-[#131A2E]"
          >
            Open Cases Directory
          </button>
        </div>
      )}

      {/* Recent Investigations List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold font-serif text-[#131A2E] uppercase tracking-wider">
            All Case Files ({cases.length})
          </h3>
          <button
            onClick={() => navigate('/cases')}
            className="text-xs text-[#C9962F] hover:underline font-medium"
          >
            Manage Directory →
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {cases.map((c) => (
            <div
              key={c.case_id}
              onClick={() => setActiveCaseId(c.case_id)}
              className={`case-card p-4 rounded-lg cursor-pointer transition ${
                c.case_id === activeCase?.case_id
                  ? 'ring-2 ring-[#C9962F]'
                  : 'hover:border-[#C9962F]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`stamp-label text-[9px] ${c.is_demo ? 'stamp-gold' : 'stamp-navy'}`}>
                  {c.is_demo ? 'DEMO' : 'USER'}
                </span>
                <span className="text-[10px] text-gray-400 font-mono">
                  {new Date(c.created_at).toLocaleDateString()}
                </span>
              </div>

              <h4 className="font-bold text-sm text-[#131A2E] mt-2 font-serif truncate">
                {c.name}
              </h4>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                {c.description || 'No description provided.'}
              </p>

              <div className="mt-3 pt-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500 font-mono">
                <span>{c.document_count} docs</span>
                <span>{c.contradiction_count} conflicts</span>
                <span className="text-[#C9962F] font-bold">
                  {c.case_id === activeCase?.case_id ? 'ACTIVE' : 'SELECT'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
