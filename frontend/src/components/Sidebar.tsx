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
} from 'lucide-react';
import { useCase } from '../context/CaseContext';

export const Sidebar: React.FC = () => {
  const { activeCase } = useCase();

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
    { to: '/cases', label: 'Cases Directory', icon: FolderArchive },
    { to: '/new', label: 'New Investigation', icon: FilePlus },
    { to: '/documents', label: 'Documents', icon: FileText, badge: activeCase?.document_count },
    { to: '/timeline', label: 'Timeline', icon: Clock, badge: activeCase?.event_count },
    { to: '/evidence', label: 'Evidence Search', icon: Search },
    { to: '/contradictions', label: 'Contradictions', icon: Scale, badge: activeCase?.contradiction_count },
    { to: '/hypotheses', label: 'Hypotheses', icon: BrainCircuit, badge: activeCase?.hypothesis_count },
    { to: '/graph', label: 'Case Graph', icon: Network },
    { to: '/report', label: 'Investigation Report', icon: FileCheck2 },
    { to: '/ask', label: 'Ask a Question', icon: HelpCircle },
    { to: '/settings', label: 'Settings & Benchmark', icon: SlidersHorizontal },
  ];

  return (
    <aside className="w-64 bg-[#131A2E] text-[#B0BBD8] min-h-[calc(100vh-4rem)] flex flex-col border-r border-[#2A344E] select-none">
      <div className="p-4 border-b border-[#2A344E]/60">
        <div className="text-[11px] uppercase font-bold tracking-widest text-[#C9962F] font-serif">
          Investigation Dossier
        </div>
        <div className="mt-1 text-sm font-semibold text-white truncate" title={activeCase?.name || 'No case selected'}>
          {activeCase?.name || 'No Active Case'}
        </div>
        <div className="text-[11px] text-[#7A8AA8] mt-0.5">
          Status: <span className="text-[#E0B354] uppercase font-medium">{activeCase?.status || 'N/A'}</span>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition ${
                  isActive
                    ? 'bg-[#C9962F] text-[#131A2E] font-bold shadow-sm'
                    : 'text-[#C5D0E8] hover:bg-[#1D2744] hover:text-white'
                }`
              }
            >
              <div className="flex items-center space-x-2.5">
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 bg-[#131A2E]/60 text-white font-mono rounded">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="p-3 border-t border-[#2A344E]/60 text-[11px] text-[#7A8AA8] bg-[#0E1424]">
        <div className="flex items-center justify-between">
          <span>Text Detective</span>
          <span className="text-[#C9962F]">CSE Research</span>
        </div>
        <p className="text-[10px] text-[#556485] mt-1">
          Lokesh M. • Punith Sai N. • Vamsika K.
        </p>
      </div>
    </aside>
  );
};
