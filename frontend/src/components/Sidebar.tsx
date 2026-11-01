import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderArchive,
  FilePlus,
  FileText,
  Clock,
  Search,
  Scale,
  BrainCircuit,
  Network,
  FileCheck2,
  HelpCircle,
  SlidersHorizontal,
  ChevronRight,
} from 'lucide-react';
import { useCase } from '../context/CaseContext';

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  exact?: boolean;
  badge?: number;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC = () => {
  const { activeCase } = useCase();

  const sections: NavSection[] = [
    {
      title: 'WORKSPACE',
      items: [
        { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
        { to: '/cases', label: 'Cases Directory', icon: FolderArchive },
        { to: '/new', label: 'New Investigation', icon: FilePlus },
      ],
    },
    {
      title: 'ANALYTICS PIPELINE',
      items: [
        { to: '/documents', label: 'Documents (M1)', icon: FileText, badge: activeCase?.document_count },
        { to: '/timeline', label: 'Timeline (M2)', icon: Clock, badge: activeCase?.event_count },
        { to: '/evidence', label: 'Evidence Search (M3)', icon: Search },
        { to: '/contradictions', label: 'Contradictions (M4)', icon: Scale, badge: activeCase?.contradiction_count },
        { to: '/hypotheses', label: 'Hypotheses (M5)', icon: BrainCircuit, badge: activeCase?.hypothesis_count },
        { to: '/graph', label: 'Case Graph', icon: Network },
      ],
    },
    {
      title: 'INTELLIGENCE & AUDIT',
      items: [
        { to: '/report', label: 'Dossier Report (M6)', icon: FileCheck2 },
        { to: '/ask', label: 'Ask a Question', icon: HelpCircle },
        { to: '/settings', label: 'Settings & Benchmark', icon: SlidersHorizontal },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 min-h-[calc(100vh-4rem)] flex flex-col border-r border-slate-800 select-none shrink-0">
      {/* Active Case Dossier Mini-Card */}
      <div className="p-3.5 m-3 rounded-xl bg-slate-800/60 border border-slate-700/60">
        <div className="flex items-center justify-between text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
          <span>Active Investigation</span>
          <span
            className={`px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
              activeCase?.status === 'completed'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : activeCase?.status === 'outdated'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
            }`}
          >
            {activeCase?.status || 'No Case'}
          </span>
        </div>
        <div className="mt-1.5 text-xs font-semibold text-white truncate" title={activeCase?.name || 'No case selected'}>
          {activeCase?.name || 'No Active Case'}
        </div>
        <div className="text-[10px] text-slate-400 mt-1 flex items-center justify-between">
          <span>{activeCase?.document_count || 0} documents</span>
          <span>{activeCase?.event_count || 0} events</span>
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 px-3 py-2 space-y-5 overflow-y-auto">
        {sections.map((sec) => (
          <div key={sec.title} className="space-y-1">
            <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              {sec.title}
            </div>
            {sec.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.exact}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white font-semibold shadow-sm'
                        : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                    }`
                  }
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <Icon className="w-4 h-4 shrink-0 opacity-80" />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span
                      className="ml-2 text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-300 font-mono rounded-full border border-slate-700 shrink-0"
                    >
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-800 text-[11px] text-slate-400 bg-slate-950/60">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-slate-300">Text Detective</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono">B.Tech Project</span>
        </div>
        <p className="text-[10px] text-slate-400 mt-1">
          Lokesh M. • Punith Sai N. • Vamsika K.
        </p>
      </div>
    </aside>
  );
};
