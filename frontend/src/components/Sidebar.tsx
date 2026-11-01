import React, { useState } from 'react';
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
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
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
  const [collapsed, setCollapsed] = useState(false);

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
        { to: '/documents', label: 'Documents', icon: FileText, badge: activeCase?.document_count },
        { to: '/timeline', label: 'Timeline', icon: Clock, badge: activeCase?.event_count },
        { to: '/evidence', label: 'Evidence Search', icon: Search },
        { to: '/contradictions', label: 'Contradictions', icon: Scale, badge: activeCase?.contradiction_count },
        { to: '/hypotheses', label: 'Hypotheses', icon: BrainCircuit, badge: activeCase?.hypothesis_count },
        { to: '/graph', label: 'Case Graph', icon: Network },
      ],
    },
    {
      title: 'INTELLIGENCE & AUDIT',
      items: [
        { to: '/report', label: 'Investigation Report', icon: FileCheck2 },
        { to: '/ask', label: 'Ask AI Assistant', icon: HelpCircle },
        { to: '/settings', label: 'Settings & Accuracy', icon: SlidersHorizontal },
      ],
    },
  ];

  return (
    <aside
      className={`bg-slate-900 text-slate-300 min-h-[calc(100vh-4rem)] flex flex-col border-r border-slate-800 select-none transition-all duration-200 shrink-0 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Active Case Header Card */}
      {!collapsed ? (
        <div className="p-3.5 m-3 rounded-xl bg-slate-800/70 border border-slate-700/60 shadow-inner">
          <div className="flex items-center justify-between text-[10px] font-bold tracking-wider text-slate-400 uppercase">
            <span>Active Case</span>
            <span
              className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
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
          <div className="mt-1.5 text-xs font-bold text-white truncate" title={activeCase?.name || 'No case selected'}>
            {activeCase?.name || 'No Active Case'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 flex items-center justify-between">
            <span>{activeCase?.document_count || 0} docs</span>
            <span>{activeCase?.contradiction_count || 0} conflicts</span>
          </div>
        </div>
      ) : (
        <div className="p-3 my-2 flex justify-center" title={activeCase?.name || 'Active Case'}>
          <div className="w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold text-xs">
            {activeCase ? activeCase.name.substring(0, 2).toUpperCase() : 'TD'}
          </div>
        </div>
      )}

      {/* Navigation Sections */}
      <nav className="flex-1 px-2.5 py-2 space-y-4 overflow-y-auto">
        {sections.map((sec) => (
          <div key={sec.title} className="space-y-1">
            {!collapsed && (
              <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {sec.title}
              </div>
            )}
            {sec.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.exact}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `flex items-center ${
                      collapsed ? 'justify-center px-2 py-2.5' : 'justify-between px-3 py-2'
                    } rounded-xl text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white font-semibold shadow-sm'
                        : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                    }`
                  }
                >
                  <div className={`flex items-center ${collapsed ? '' : 'space-x-2.5'} min-w-0`}>
                    <Icon className="w-4 h-4 shrink-0 opacity-80" />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                  </div>
                  {!collapsed && item.badge !== undefined && item.badge > 0 && (
                    <span className="ml-2 text-[10px] px-2 py-0.5 bg-slate-800 text-slate-300 font-mono rounded-full border border-slate-700 shrink-0">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Clean Enterprise Footer with Collapse Button */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/70 flex items-center justify-between text-xs">
        {!collapsed && (
          <div className="flex items-center space-x-2 text-slate-400 text-[11px]">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="font-medium text-slate-300">System Ready</span>
            <span className="text-[10px] text-slate-400 font-mono">v1.2</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={`p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition ${
            collapsed ? 'mx-auto' : ''
          }`}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
};
