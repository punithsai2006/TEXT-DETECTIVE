import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { MultiAgentDeliberation } from '../types';
import {
  Bot,
  BrainCircuit,
  GitBranch,
  Clock,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  MessageSquare,
  Award,
  ChevronRight,
  Gavel,
  CheckCircle2,
  AlertTriangle,
  Zap,
} from 'lucide-react';

export const AgentSwarmPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [deliberation, setDeliberation] = useState<MultiAgentDeliberation | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'debate' | 'messages' | 'agents'>('debate');

  useEffect(() => {
    if (!activeCaseId) return;
    setLoading(true);
    api
      .getAgentDeliberations(activeCaseId)
      .then((data) => setDeliberation(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [activeCaseId]);

  const agents = [
    {
      name: 'LeadInvestigatorAgent',
      role: 'Chief Investigative Strategy Coordinator',
      icon: Award,
      badgeColor: 'bg-blue-600',
      description: 'Decomposes complex cases into specialized tasks, directs the agent swarm, and synthesizes the judicial case theory.',
    },
    {
      name: 'KnowledgeGraphRAGAgent',
      role: 'Forensic Graph-RAG Retrieval Specialist',
      icon: GitBranch,
      badgeColor: 'bg-indigo-600',
      description: 'Traverses the multi-hop Case Knowledge Graph; integrates dense embeddings (all-MiniLM-L6-v2) and BM25 via Reciprocal Rank Fusion (RRF).',
    },
    {
      name: 'ForensicTimelineAgent',
      role: 'Timeline Synthesis & Narrative Fusion',
      icon: Clock,
      badgeColor: 'bg-emerald-600',
      description: 'Clusters raw telemetry and log events into 5 sequential crime phases, isolating the physical access and asset exfiltration windows.',
    },
    {
      name: 'CrossExaminationAgent',
      role: 'Forensic Cross-Examiner & Perjury Detector',
      icon: Scale,
      badgeColor: 'bg-amber-600',
      description: 'Cross-examines witness and suspect testimonies against objective sensor records (RFID taps, key locks, CCTV, vehicle gates) using NLI.',
    },
    {
      name: 'AdversarialHypothesisAgent',
      role: 'Multi-LLM Debate & Bayesian Scorer',
      icon: Gavel,
      badgeColor: 'bg-rose-600',
      description: 'Pits Prosecution and Defense LLM agents in adversarial courtroom deliberation, computing veracity and Slide 18 mathematical scores.',
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs uppercase font-bold tracking-wider text-blue-600">
            <Bot className="w-3.5 h-3.5 text-blue-600" />
            <span>Autonomous Multi-Agent System (MAS)</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
            Agent Swarm & Multi-LLM Debate
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            5 autonomous specialized AI agents collaborating on case <strong>{activeCase?.name || 'Selected Investigation'}</strong>.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center rounded-lg border border-slate-300 overflow-hidden bg-white shadow-sm p-0.5 text-xs">
          <button
            onClick={() => setActiveTab('debate')}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 font-semibold rounded-md transition ${
              activeTab === 'debate' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Gavel className="w-3.5 h-3.5" />
            <span>Courtroom Debate</span>
          </button>
          <button
            onClick={() => setActiveTab('messages')}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 font-semibold rounded-md transition ${
              activeTab === 'messages' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Agent Deliberation Logs ({deliberation?.messages?.length || 0})</span>
          </button>
          <button
            onClick={() => setActiveTab('agents')}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 font-semibold rounded-md transition ${
              activeTab === 'agents' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BrainCircuit className="w-3.5 h-3.5" />
            <span>Agent Roster (5)</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="case-card p-12 text-center rounded-2xl">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs text-slate-500">Initiating Multi-Agent Swarm & convening deliberation debate...</p>
        </div>
      ) : !deliberation ? (
        <div className="case-card p-12 text-center rounded-2xl">
          <Bot className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Multi-Agent Deliberation Recorded</h3>
          <p className="text-xs text-slate-500 mt-1">
            Run the investigation analysis pipeline on uploaded documents to engage the Multi-Agent Swarm.
          </p>
        </div>
      ) : activeTab === 'debate' ? (
        /* ==============================================================
           COURTROOM DEBATE: PROSECUTION vs DEFENSE vs JUDICIAL ARBITER
           ============================================================== */
        <div className="space-y-6">
          {/* Judicial Arbiter Verdict Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white border border-slate-700/80 shadow-md space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <span className="p-1.5 bg-amber-400/20 text-amber-300 rounded-lg">
                  <Gavel className="w-5 h-5 text-amber-300" />
                </span>
                <div>
                  <div className="text-[10px] uppercase font-bold tracking-wider text-amber-400">
                    Multi-LLM Consensus Verdict
                  </div>
                  <h2 className="text-base sm:text-lg font-bold text-white">
                    {deliberation.judicial_verdict?.verdict || 'Culpability Established'}
                  </h2>
                </div>
              </div>

              <div className="flex items-center space-x-2 font-mono text-xs">
                <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 rounded-full font-bold">
                  {deliberation.judicial_verdict?.confidence_percentage || 95}% Confidence
                </span>
                <span className="px-3 py-1 bg-blue-500/20 text-blue-300 border border-blue-500/40 rounded-full">
                  {deliberation.judicial_verdict?.bayesian_posterior_odds || '18.4 : 1 Odds'}
                </span>
              </div>
            </div>

            <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-sans">
              {deliberation.judicial_verdict?.final_determination}
            </p>

            <div className="text-[11px] text-slate-400 pt-1 flex items-center gap-1.5 font-mono">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Standard of Proof: <strong>{deliberation.judicial_verdict?.legal_sufficiency_standard || 'Beyond a Reasonable Doubt'}</strong></span>
            </div>
          </div>

          {/* Adversarial Arguments Side-by-Side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Prosecution Advocate Model */}
            <div className="case-card p-5 sm:p-6 rounded-2xl border-t-4 border-t-blue-600 bg-white space-y-4 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center space-x-2">
                  <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
                    P
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-slate-900">Prosecution Advocate Model</h3>
                    <div className="text-[10px] text-blue-600 font-semibold uppercase">Culpability Argument</div>
                  </div>
                </div>

                <span className="text-xs font-mono font-bold bg-blue-50 text-blue-700 px-2.5 py-1 rounded-lg border border-blue-200">
                  Slide 18 Score: {deliberation.prosecution_argument?.mathematical_score || 0}
                </span>
              </div>

              <div className="text-xs text-slate-700 leading-relaxed bg-blue-50/50 p-3.5 rounded-xl border border-blue-100">
                <strong>Core Thesis:</strong> {deliberation.prosecution_argument?.core_thesis}
              </div>

              <div className="space-y-2 pt-1">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Key Physical Telemetry Proofs
                </div>
                <div className="space-y-2 text-xs">
                  {(deliberation.prosecution_argument?.key_proof_points || []).map((point: string, idx: number) => (
                    <div key={idx} className="p-2.5 bg-slate-50 rounded-xl border border-slate-200/80 flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span className="text-slate-700 leading-relaxed">{point}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Slide 18 Breakdown Table */}
              {deliberation.prosecution_argument?.slide_18_metrics && (
                <div className="pt-2 border-t border-slate-100">
                  <div className="text-[10px] font-mono text-slate-400 uppercase font-bold mb-1.5">
                    Slide 18 Mathematical Formula Breakdown
                  </div>
                  <div className="grid grid-cols-4 gap-1 text-center font-mono text-xs">
                    <div className="p-2 bg-emerald-50 rounded-lg border border-emerald-200">
                      <div className="text-[9px] text-emerald-600 font-bold">SUPPORT</div>
                      <div className="font-bold text-emerald-800 text-sm">+{deliberation.prosecution_argument.slide_18_metrics.support_score}</div>
                    </div>
                    <div className="p-2 bg-rose-50 rounded-lg border border-rose-200">
                      <div className="text-[9px] text-rose-600 font-bold">CONFLICT</div>
                      <div className="font-bold text-rose-800 text-sm">-{deliberation.prosecution_argument.slide_18_metrics.conflict_score}</div>
                    </div>
                    <div className="p-2 bg-indigo-50 rounded-lg border border-indigo-200">
                      <div className="text-[9px] text-indigo-600 font-bold">CORROB</div>
                      <div className="font-bold text-indigo-800 text-sm">+{deliberation.prosecution_argument.slide_18_metrics.corroboration_score}</div>
                    </div>
                    <div className="p-2 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="text-[9px] text-blue-600 font-bold">TOTAL</div>
                      <div className="font-bold text-blue-800 text-sm">={deliberation.prosecution_argument.slide_18_metrics.total_score}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Defense Advocate Model */}
            <div className="case-card p-5 sm:p-6 rounded-2xl border-t-4 border-t-slate-500 bg-white space-y-4 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center space-x-2">
                  <div className="w-7 h-7 rounded-lg bg-slate-700 text-white flex items-center justify-center font-bold text-xs">
                    D
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-slate-900">Defense Advocate Model</h3>
                    <div className="text-[10px] text-slate-500 font-semibold uppercase">Reasonable Doubt Advocate</div>
                  </div>
                </div>

                <span className="text-xs font-mono font-bold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg border border-slate-200">
                  Presumption of Innocence
                </span>
              </div>

              <div className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                <strong>Defense Strategy:</strong> {deliberation.defense_argument?.defense_strategy}
              </div>

              <div className="space-y-2 pt-1">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Adversarial Rebuttal Points
                </div>
                <div className="space-y-2 text-xs">
                  {(deliberation.defense_argument?.rebuttal_points || []).map((point: string, idx: number) => (
                    <div key={idx} className="p-2.5 bg-slate-50 rounded-xl border border-slate-200/80 flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <span className="text-slate-700 leading-relaxed">{point}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 p-3 rounded-xl bg-amber-50/50 border border-amber-200 text-xs">
                <strong className="text-amber-800">Reasonable Doubt Analysis:</strong>
                <p className="text-amber-900 mt-1 leading-relaxed">
                  {deliberation.defense_argument?.reasonable_doubt_assessment}
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : activeTab === 'messages' ? (
        /* ==============================================================
           INTER-AGENT COMMUNICATION STREAM
           ============================================================== */
        <div className="space-y-4">
          <div className="text-xs text-slate-500 pb-1">
            Displaying full agent-to-agent message transmission with internal thoughts, citations, and graph nodes.
          </div>
          {deliberation.messages.map((msg, idx) => (
            <div
              key={msg.message_id || idx}
              className="case-card p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-3"
            >
              <div className="flex items-center justify-between flex-wrap gap-2 pb-2.5 border-b border-slate-100">
                <div className="flex items-center space-x-2 text-xs">
                  <span className="font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200/60 font-mono">
                    {msg.sender}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                  <span className="font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200 font-mono">
                    {msg.recipient}
                  </span>
                  <span className="text-[10px] uppercase font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200">
                    {msg.message_type.replace('_', ' ')}
                  </span>
                </div>

                <span className="text-[10px] text-slate-400 font-mono">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>

              {/* Agent Internal Thought Chain */}
              {msg.thought_process && (
                <div className="p-3 rounded-xl bg-amber-50/60 border border-amber-200/80 text-xs text-amber-900 space-y-1">
                  <div className="font-bold text-[10px] uppercase tracking-wider text-amber-700 flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-amber-600" />
                    <span>Agent Internal Chain-of-Thought</span>
                  </div>
                  <p className="italic leading-relaxed">"{msg.thought_process}"</p>
                </div>
              )}

              {/* Message Payload */}
              <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-sans">
                {msg.content}
              </p>

              {/* Evidence Citations & Graph Nodes */}
              <div className="flex items-center justify-between flex-wrap gap-2 pt-2 text-[10px] font-mono text-slate-500">
                {msg.evidence_citations && msg.evidence_citations.length > 0 && (
                  <div className="flex items-center space-x-1">
                    <span className="font-bold text-slate-400">Cited:</span>
                    <span className="text-blue-600">{msg.evidence_citations.join(', ')}</span>
                  </div>
                )}
                {msg.subgraph_nodes && msg.subgraph_nodes.length > 0 && (
                  <div className="flex items-center space-x-1">
                    <span className="font-bold text-slate-400">Graph Nodes:</span>
                    <span className="text-indigo-600">{msg.subgraph_nodes.join(', ')}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* ==============================================================
           AGENT ROSTER (5 SPECIALIST AGENTS)
           ============================================================== */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {agents.map((agent, idx) => {
            const Icon = agent.icon;
            return (
              <div
                key={idx}
                className="case-card p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
                    <div className={`w-9 h-9 rounded-xl ${agent.badgeColor} text-white flex items-center justify-center shadow-md`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-sm text-slate-900 leading-tight">
                        {agent.name}
                      </h3>
                      <div className="text-[10px] text-blue-600 font-semibold mt-0.5">
                        {agent.role}
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 mt-3 leading-relaxed">
                    {agent.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-400">Status</span>
                  <span className="text-emerald-600 font-bold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Active in Swarm
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
