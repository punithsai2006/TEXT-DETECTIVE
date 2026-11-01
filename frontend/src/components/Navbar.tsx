import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, ShieldAlert, Cpu, FolderOpen, PlusCircle, AlertCircle, ChevronDown, CheckCircle2 } from 'lucide-react';
import { useCase } from '../context/CaseContext';

export const Navbar: React.FC = () => {
  const { cases, activeCaseId, activeCase, setActiveCaseId, health } = useCase();
  const navigate = useNavigate();

  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand / Logo */}
        <Link to="/" className="flex items-center space-x-3 group shrink-0">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform duration-200">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="tracking-tight text-base font-bold text-white flex items-center gap-2">
              <span>TEXT DETECTIVE</span>
              <span className="text-[10px] tracking-normal font-sans px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/25 font-semibold">
                AGENTIC AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-normal hidden sm:block">
              Evidence-Based Investigation & Analytics
            </p>
          </div>
        </Link>

        {/* Center: Case Selector */}
        <div className="flex items-center space-x-2.5 flex-1 max-w-md justify-center">
          <div className="flex items-center bg-slate-800/90 border border-slate-700/80 hover:border-slate-600 rounded-lg px-3 py-1.5 shadow-inner transition-colors w-full">
            <FolderOpen className="w-4 h-4 text-blue-400 mr-2 shrink-0" />
            <select
              value={activeCaseId || ''}
              onChange={(e) => {
                setActiveCaseId(e.target.value || null);
              }}
              className="bg-transparent text-xs sm:text-sm text-slate-100 focus:outline-none cursor-pointer w-full font-medium truncate"
              aria-label="Select active investigation case"
            >
              {cases.length === 0 ? (
                <option value="" disabled className="bg-slate-900 text-slate-400">No cases available</option>
              ) : (
                cases.map((c) => (
                  <option key={c.case_id} value={c.case_id} className="bg-slate-900 text-slate-100">
                    {c.name} {c.is_demo ? '• (Benchmark Demo)' : ''}
                  </option>
                ))
              )}
            </select>
          </div>

          {activeCase?.is_demo && (
            <span className="hidden lg:inline-flex items-center text-[10px] font-semibold tracking-wide px-2 py-1 bg-amber-500/15 text-amber-300 border border-amber-500/30 rounded-full shrink-0">
              Demo Benchmark
            </span>
          )}

          {activeCase?.single_document_warning && (
            <span className="hidden xl:inline-flex items-center text-[10px] px-2 py-1 bg-rose-500/15 text-rose-300 border border-rose-500/30 rounded-full shrink-0" title="Cross-document contradictions require at least 2 files.">
              <AlertCircle className="w-3 h-3 mr-1" /> Single Document
            </span>
          )}
        </div>

        {/* Right Actions: LLM Provider & New Investigation */}
        <div className="flex items-center space-x-3 shrink-0">
          <div className="hidden md:flex items-center text-xs text-slate-300 bg-slate-800/80 px-2.5 py-1.5 rounded-lg border border-slate-700/70">
            <span className={`w-2 h-2 rounded-full mr-2 ${health?.is_mock ? 'bg-amber-400' : 'bg-emerald-400 animate-pulse'}`} />
            <span className="text-slate-400 mr-1.5">Model:</span>
            <strong className="text-white font-mono text-[11px]">{health?.llm_provider?.toUpperCase() || 'MOCK'}</strong>
            {health?.is_mock && <span className="text-amber-400 text-[10px] ml-1.5">(Offline)</span>}
          </div>

          <button
            onClick={() => navigate('/new')}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white transition-all shadow-sm hover:shadow"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Case</span>
          </button>
        </div>
      </div>
    </header>
  );
};
