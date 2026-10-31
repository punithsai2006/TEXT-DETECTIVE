import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, ShieldAlert, Cpu, FolderOpen, PlusCircle, AlertCircle } from 'lucide-react';
import { useCase } from '../context/CaseContext';

export const Navbar: React.FC = () => {
  const { cases, activeCaseId, activeCase, setActiveCaseId, health } = useCase();
  const navigate = useNavigate();

  return (
    <header className="bg-[#131A2E] text-white border-b border-[#2A344E] sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand / Logo */}
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded bg-[#C9962F] flex items-center justify-center text-[#131A2E] font-bold shadow-md group-hover:bg-[#E0B354] transition">
            <Search className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div>
            <div className="font-serif tracking-wider text-lg font-bold text-[#F4F0E6] flex items-center gap-2">
              TEXT DETECTIVE
              <span className="text-[10px] tracking-normal font-sans px-1.5 py-0.5 rounded bg-[#C9962F]/20 text-[#C9962F] border border-[#C9962F]/30 uppercase font-semibold">
                v1.0
              </span>
            </div>
            <p className="text-[11px] text-[#A6B2D1] tracking-wide font-sans">
              Evidence-Based Investigation Framework
            </p>
          </div>
        </Link>

        {/* Center: Case Selector */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center bg-[#1D2744] border border-[#313E61] rounded-md px-3 py-1.5 shadow-inner">
            <FolderOpen className="w-4 h-4 text-[#C9962F] mr-2" />
            <select
              value={activeCaseId || ''}
              onChange={(e) => {
                setActiveCaseId(e.target.value || null);
              }}
              className="bg-transparent text-sm text-[#F4F0E6] focus:outline-none cursor-pointer pr-4 font-medium"
            >
              {cases.length === 0 ? (
                <option value="" disabled className="bg-[#131A2E]">No cases available</option>
              ) : (
                cases.map((c) => (
                  <option key={c.case_id} value={c.case_id} className="bg-[#131A2E] text-white">
                    {c.name} {c.is_demo ? '• (Demo)' : ''}
                  </option>
                ))
              )}
            </select>
          </div>

          {activeCase?.is_demo && (
            <span className="hidden md:inline-flex items-center text-[10px] uppercase font-bold tracking-wider px-2 py-1 bg-[#C9962F]/20 text-[#E0B354] border border-[#C9962F]/40 rounded">
              Demo Data • Fictional Case
            </span>
          )}

          {activeCase?.single_document_warning && (
            <span className="inline-flex items-center text-[11px] px-2 py-0.5 bg-amber-500/10 text-amber-300 border border-amber-500/30 rounded" title="Cross-document contradictions cannot be evaluated with a single file.">
              <AlertCircle className="w-3 h-3 mr-1" /> Single Doc
            </span>
          )}
        </div>

        {/* Right Actions: LLM Provider & New Investigation */}
        <div className="flex items-center space-x-3">
          <div className="hidden lg:flex items-center text-xs text-[#A6B2D1] bg-[#172037] px-2.5 py-1 rounded border border-[#2B3754]">
            <Cpu className="w-3.5 h-3.5 text-[#C9962F] mr-1.5" />
            <span>
              LLM: <strong className="text-white">{health?.llm_provider?.toUpperCase() || 'MOCK'}</strong>
              {health?.is_mock && <span className="text-[#E0B354] ml-1">(Offline)</span>}
            </span>
          </div>

          <button
            onClick={() => navigate('/new')}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-[#C9962F] text-[#131A2E] hover:bg-[#E0B354] transition shadow"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Case</span>
          </button>
        </div>
      </div>
    </header>
  );
};
