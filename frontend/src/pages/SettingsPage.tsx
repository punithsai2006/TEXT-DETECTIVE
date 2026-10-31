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
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
          Configuration & Research Benchmarks
        </div>
        <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
          Settings & Evaluation Framework
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          LLM provider runtime status, model parameters, and reproducible accuracy evaluation.
        </p>
      </div>

      {/* Provider Status Card */}
      <div className="case-card p-5 rounded-lg space-y-4">
        <div className="flex items-center space-x-2 pb-2 border-b border-gray-100">
          <Cpu className="w-4 h-4 text-[#C9962F]" />
          <h3 className="font-serif font-bold text-sm text-[#131A2E]">
            Active LLM Runtime Provider
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="bg-[#FAF8F3] p-3 rounded">
            <span className="text-gray-500 text-[11px]">Provider</span>
            <div className="text-sm font-bold text-[#131A2E] font-mono mt-0.5 uppercase">
              {health?.llm_provider || 'MOCK'}
            </div>
            <div className="text-[10px] text-gray-400 mt-1">Configured in backend .env</div>
          </div>

          <div className="bg-[#FAF8F3] p-3 rounded">
            <span className="text-gray-500 text-[11px]">Model Architecture</span>
            <div className="text-sm font-bold text-[#131A2E] font-mono mt-0.5">
              {health?.llm_model || 'mock-investigator-v1'}
            </div>
            <div className="text-[10px] text-gray-400 mt-1">
              {health?.is_mock ? 'Offline Deterministic Engine' : 'Live Cloud API'}
            </div>
          </div>

          <div className="bg-[#FAF8F3] p-3 rounded">
            <span className="text-gray-500 text-[11px]">Demo Mode</span>
            <div className="text-sm font-bold text-emerald-700 font-mono mt-0.5">
              {health?.demo_mode ? 'ENABLED (Self-Contained)' : 'PRODUCTION'}
            </div>
            <div className="text-[10px] text-gray-400 mt-1">Synthetic benchmarks isolated</div>
          </div>
        </div>

        <div className="text-[11px] text-gray-500 bg-gray-50 p-2.5 rounded border border-gray-200">
          To switch providers, update <code>backend/.env</code> with <code>LLM_PROVIDER=anthropic</code> or <code>LLM_PROVIDER=openai</code> along with your API key. Offline testing requires zero API credentials.
        </div>
      </div>

      {/* Automated Benchmark Runner */}
      <div className="case-card p-5 rounded-lg space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-gray-100">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-[#C9962F]" />
            <h3 className="font-serif font-bold text-sm text-[#131A2E]">
              Reproducible Evaluation Harness (Slide 11)
            </h3>
          </div>

          <button
            onClick={runEvaluation}
            disabled={evaluating}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-[#131A2E] text-white text-xs font-bold rounded hover:bg-[#1D2744] transition disabled:opacity-50"
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
              <div className="bg-[#FAF8F3] p-2.5 rounded border border-gray-200">
                <span className="text-[10px] text-gray-500 uppercase font-bold">Evaluated Cases</span>
                <div className="text-xl font-bold font-mono text-[#131A2E] mt-0.5">
                  {benchmarkData.total_cases_evaluated}
                </div>
              </div>

              <div className="bg-[#FAF8F3] p-2.5 rounded border border-gray-200">
                <span className="text-[10px] text-gray-500 uppercase font-bold">Total Documents</span>
                <div className="text-xl font-bold font-mono text-[#131A2E] mt-0.5">
                  {benchmarkData.total_documents}
                </div>
              </div>

              <div className="bg-[#FAF8F3] p-2.5 rounded border border-emerald-300 bg-emerald-50/50">
                <span className="text-[10px] text-emerald-800 uppercase font-bold">Hypothesis Accuracy</span>
                <div className="text-xl font-bold font-mono text-emerald-700 mt-0.5">
                  {benchmarkData.hypothesis_accuracy_top1_percent}%
                </div>
              </div>

              <div className="bg-[#FAF8F3] p-2.5 rounded border border-gray-200">
                <span className="text-[10px] text-gray-500 uppercase font-bold">Held-Out Test Case</span>
                <div className="text-xl font-bold font-mono text-purple-700 mt-0.5">
                  Case 03 (Helios)
                </div>
              </div>
            </div>

            {/* Breakdown table */}
            <div className="overflow-x-auto border border-gray-200 rounded">
              <table className="w-full text-left font-serif">
                <thead className="bg-[#FAF8F3] text-[10px] font-mono uppercase text-gray-600 border-b">
                  <tr>
                    <th className="p-2">Case ID</th>
                    <th className="p-2">Case Name</th>
                    <th className="p-2">Held-Out?</th>
                    <th className="p-2 text-right">Entity F1</th>
                    <th className="p-2 text-right">Timeline Acc</th>
                    <th className="p-2 text-right">Retrieval MRR</th>
                    <th className="p-2 text-right">Top Hyp Rank</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-xs">
                  {benchmarkData.case_results?.map((r: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="p-2 font-mono text-[11px] text-gray-500">{r.case_id}</td>
                      <td className="p-2 font-medium text-[#131A2E]">{r.case_name}</td>
                      <td className="p-2 text-gray-600">{r.is_held_out ? 'Yes (Held-Out)' : 'No'}</td>
                      <td className="p-2 text-right font-mono">{r.entity_metrics?.f1?.toFixed(2)}</td>
                      <td className="p-2 text-right font-mono">{(r.timeline_order_accuracy * 100).toFixed(1)}%</td>
                      <td className="p-2 text-right font-mono">{r.retrieval_metrics?.mrr?.toFixed(2)}</td>
                      <td className="p-2 text-right font-bold text-emerald-700">
                        {r.hypothesis_top1_correct ? 'Rank #1 (PASSED)' : 'FAILED'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="p-6 text-center text-gray-400 text-xs">
            No benchmark report currently loaded. Click "Execute Benchmark Script" to run evaluation.
          </div>
        )}
      </div>

      {/* Human Evaluation Template Card */}
      <div className="case-card p-5 rounded-lg flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-gray-800 font-serif">
            <FileSpreadsheet className="w-4 h-4 text-[#C9962F]" />
            <span>Human Evaluation Protocol (1–5 Clarity & Traceability)</span>
          </div>
          <p className="text-xs text-gray-500 mt-1 max-w-md">
            Evaluation form template for human analysts to rate report readability and citation validity.
          </p>
        </div>

        <a
          href="/docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv"
          download
          className="px-3 py-1.5 border border-gray-300 rounded text-xs font-medium text-gray-700 hover:bg-gray-50 transition"
        >
          Download CSV Form
        </a>
      </div>

      {/* Authorship & Academic Identity */}
      <div className="case-card p-5 rounded-lg border-t-4 border-t-[#C9962F] text-xs space-y-2">
        <h4 className="font-serif font-bold text-[#131A2E] uppercase tracking-wide">
          Text Detective Project Attribution
        </h4>
        <p className="text-gray-600 leading-relaxed font-serif">
          Presented at CSE Research Showcase: <em>Text Detective: An Agentic Text Analytics Framework for Evidence-Based Investigation</em>.
        </p>
        <div className="pt-2 border-t border-gray-100 flex items-center space-x-6 text-[11px] text-gray-500 font-mono">
          <span>Makka Lokesh (AM.SC.U4CSE24233)</span>
          <span>Punith Sai Nallapaneni (AM.SC.U4CSE24337)</span>
          <span>Vamsika Kilari (AM.SC.U4CSE24227)</span>
        </div>
      </div>
    </div>
  );
};
