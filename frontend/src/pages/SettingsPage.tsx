import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import {
  SlidersHorizontal,
  Cpu,
  BarChart3,
  Play,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  RefreshCw,
  Award,
  ShieldCheck,
  Download,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { health } = useCase();
  const [evaluating, setEvaluating] = useState(false);
  const [benchmarkData, setBenchmarkData] = useState<any>(null);

  const runEvaluation = async () => {
    setEvaluating(true);
    try {
      const res = await fetch('/api/evaluate', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setBenchmarkData(data);
      } else {
        // Fallback: load static benchmark report
        loadStaticBenchmark();
      }
    } catch {
      loadStaticBenchmark();
    } finally {
      setEvaluating(false);
    }
  };

  const loadStaticBenchmark = async () => {
    try {
      const res = await fetch('/docs/evaluation/benchmark_results.json');
      if (res.ok) {
        const data = await res.json();
        setBenchmarkData(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadStaticBenchmark();
  }, []);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
          Configuration & Research Benchmarks (Slide 11)
        </div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
          Settings & Evaluation Framework
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          LLM provider runtime status, model parameters, and reproducible accuracy evaluation.
        </p>
      </div>

      {/* Provider Status Card */}
      <div className="case-card p-5 sm:p-6 rounded-2xl space-y-4 shadow-sm border border-slate-200/80">
        <div className="flex items-center space-x-2 pb-2.5 border-b border-slate-100">
          <Cpu className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-sm text-slate-900">
            Active LLM Runtime Provider
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 text-xs">
          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/60">
            <span className="text-slate-500 text-[11px] font-medium">Provider</span>
            <div className="text-sm font-bold text-slate-900 font-mono mt-1 uppercase">
              {health?.llm_provider || 'MOCK'}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">Configured in backend .env</div>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/60">
            <span className="text-slate-500 text-[11px] font-medium">Model Architecture</span>
            <div className="text-sm font-bold text-slate-900 font-mono mt-1">
              {health?.llm_model || 'mock-investigator-v1'}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">
              {health?.is_mock ? 'Offline Deterministic Engine' : 'Live Cloud API'}
            </div>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/60">
            <span className="text-slate-500 text-[11px] font-medium">Environment Mode</span>
            <div className="text-sm font-bold text-emerald-700 font-mono mt-1">
              {health?.demo_mode ? 'BENCHMARK (Self-Contained)' : 'PRODUCTION'}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">Synthetic benchmarks isolated</div>
          </div>
        </div>

        <div className="text-[11px] text-slate-600 bg-blue-50/50 p-3 rounded-xl border border-blue-100">
          To switch providers, update <code>backend/.env</code> with <code>LLM_PROVIDER=groq</code> or <code>LLM_PROVIDER=openai</code> along with your API key. Offline testing requires zero API credentials.
        </div>
      </div>

      {/* Automated Benchmark Runner */}
      <div className="case-card p-5 sm:p-6 rounded-2xl space-y-4 shadow-sm border border-slate-200/80">
        <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 flex-wrap gap-2">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-blue-600" />
            <h3 className="font-bold text-sm text-slate-900">
              Reproducible Evaluation Harness (Slide 11)
            </h3>
          </div>

          <button
            onClick={runEvaluation}
            disabled={evaluating}
            className="flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl transition disabled:opacity-50 shadow-sm"
          >
            {evaluating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Evaluating Cases...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Execute Benchmark Script</span>
              </>
            )}
          </button>
        </div>

        {/* Metrics Summary Table */}
        {benchmarkData ? (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
                <span className="text-[10px] text-slate-500 uppercase font-bold">Evaluated Cases</span>
                <div className="text-xl font-bold font-mono text-slate-900 mt-0.5">
                  {benchmarkData.total_cases_evaluated}
                </div>
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/60">
                <span className="text-[10px] text-slate-500 uppercase font-bold">Total Documents</span>
                <div className="text-xl font-bold font-mono text-slate-900 mt-0.5">
                  {benchmarkData.total_documents}
                </div>
              </div>

              <div className="bg-emerald-50/70 p-3 rounded-xl border border-emerald-200/80">
                <span className="text-[10px] text-emerald-800 uppercase font-bold">Hypothesis Top-1 Accuracy</span>
                <div className="text-xl font-bold font-mono text-emerald-600 mt-0.5">
                  {benchmarkData.hypothesis_accuracy_top1_percent}%
                </div>
              </div>

              <div className="bg-purple-50/70 p-3 rounded-xl border border-purple-200/80">
                <span className="text-[10px] text-purple-800 uppercase font-bold">Held-Out Test Case</span>
                <div className="text-base font-bold font-mono text-purple-700 mt-1">
                  Case 03 (Helios)
                </div>
              </div>
            </div>

            {/* Breakdown table */}
            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-[10px] font-mono uppercase text-slate-600 border-b border-slate-200">
                  <tr>
                    <th className="p-2.5">Case ID</th>
                    <th className="p-2.5">Case Name</th>
                    <th className="p-2.5">Held-Out?</th>
                    <th className="p-2.5 text-right">Entity F1</th>
                    <th className="p-2.5 text-right">Timeline Acc</th>
                    <th className="p-2.5 text-right">Retrieval MRR</th>
                    <th className="p-2.5 text-right">Top Hyp Rank</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {benchmarkData.case_results?.map((r: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="p-2.5 font-mono text-[11px] text-slate-500">{r.case_id}</td>
                      <td className="p-2.5 font-medium text-slate-900">{r.case_name}</td>
                      <td className="p-2.5 text-slate-600">{r.is_held_out ? 'Yes (Held-Out)' : 'No'}</td>
                      <td className="p-2.5 text-right font-mono text-slate-700">{r.entity_metrics?.f1?.toFixed(2)}</td>
                      <td className="p-2.5 text-right font-mono text-slate-700">{(r.timeline_order_accuracy * 100).toFixed(1)}%</td>
                      <td className="p-2.5 text-right font-mono text-slate-700">{r.retrieval_metrics?.mrr?.toFixed(2)}</td>
                      <td className="p-2.5 text-right font-bold text-emerald-600">
                        {r.hypothesis_top1_correct ? 'Rank #1 (PASSED)' : 'FAILED'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400 text-xs">
            No benchmark report currently loaded. Click "Execute Benchmark Script" to run evaluation.
          </div>
        )}
      </div>

      {/* Human Evaluation Template Card */}
      <div className="case-card p-5 rounded-2xl flex items-center justify-between shadow-sm border border-slate-200/80 flex-wrap gap-3">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-900">
            <FileSpreadsheet className="w-4 h-4 text-blue-600" />
            <span>Human Evaluation Protocol (1–5 Clarity & Traceability)</span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-md">
            Standardized evaluation form for human investigators to rate report readability and citation validity.
          </p>
        </div>

        <a
          href="/docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv"
          download
          className="flex items-center space-x-1.5 px-3.5 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-sm"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download CSV Form</span>
        </a>
      </div>

      {/* Authorship & Academic Identity */}
      <div className="case-card p-5 sm:p-6 rounded-2xl border-l-4 border-l-blue-600 text-xs space-y-2 shadow-sm border-slate-200/80">
        <h4 className="font-bold text-slate-900 uppercase tracking-wide">
          Text Detective Project Attribution
        </h4>
        <p className="text-slate-600 leading-relaxed">
          Presented at CSE Research Showcase: <em>Text Detective: An Agentic Text Analytics Framework for Evidence-Based Investigation</em>.
        </p>
        <div className="pt-2.5 border-t border-slate-100 flex items-center flex-wrap gap-4 text-[11px] text-slate-500 font-mono">
          <span>Makka Lokesh (AM.SC.U4CSE24233)</span>
          <span>•</span>
          <span>Punith Sai Nallapaneni (AM.SC.U4CSE24337)</span>
          <span>•</span>
          <span>Vamsika Kilari (AM.SC.U4CSE24227)</span>
        </div>
      </div>
    </div>
  );
};
