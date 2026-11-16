import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { SourceCitation } from '../components/SourceCitation';
import { HypothesisCard } from '../components/HypothesisCard';
import { Link } from 'react-router-dom';
import { InvestigationReport } from '../types';
import {
  FileCheck2,
  Download,
  Printer,
  FileCode,
  FileText,
  Award,
  AlertTriangle,
  Scale,
  Clock,
  Shield,
  HelpCircle,
  Copy,
  Check,
  ShieldCheck,
  ShieldAlert,
  User,
  Cpu,
  Sparkles,
} from 'lucide-react';

export const ReportPage: React.FC = () => {
  const { activeCaseId, activeCase, refreshCases } = useCase();
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'markdown' | 'json'>('preview');
  const [markdownText, setMarkdownText] = useState<string>('');
  const [selectedCitation, setSelectedCitation] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const generate = async () => {
    if (!activeCaseId) return;
    setGenerating(true); setError('');
    try {
      const generated = await api.generateReport(activeCaseId);
      setReport(generated); setActiveTab('preview');
      const markdown = await fetch(api.getReportDownloadUrl(activeCaseId, 'markdown'));
      if (!markdown.ok) throw new Error('Report is not available for download');
      setMarkdownText(await markdown.text()); await refreshCases();
    } catch (e) { setError(e instanceof Error ? e.message : 'Report generation failed'); }
    finally { setGenerating(false); }
  };

  useEffect(() => {
    if (!activeCaseId) return;
    setLoading(true);
    api
      .getReport(activeCaseId)
      .then((rep) => {
        setReport(rep);
        // Fetch raw markdown for direct inspection
        fetch(api.getReportDownloadUrl(activeCaseId, 'markdown'))
          .then((r) => r.text())
          .then((text) => setMarkdownText(text))
          .catch(() => {});
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [activeCaseId]);

  const copyMarkdown = () => {
    navigator.clipboard.writeText(markdownText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!report) {
    return (
      <div className="case-card p-12 text-center rounded-2xl text-slate-500 text-xs">
        <FileCheck2 className="w-12 h-12 text-slate-300 mx-auto mb-2" />
        <h3 className="text-base font-bold text-slate-800">No Final Report Available</h3>
        <p className="text-xs text-slate-500 mt-1">
          Run the investigation pipeline in "New Investigation" or Dashboard to generate the full dossier.
        </p>
        {error && <p role="alert" className="text-red-700 my-3">{error}</p>}
        <button disabled={generating || !activeCaseId} onClick={generate} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg">{generating ? 'Generating…' : 'Generate Report / Retry Synthesis'}</button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {error && <p role="alert" className="text-red-700 bg-red-50 p-3 rounded-lg">{error}</p>}
      {/* Header & Export Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
            Traceable Forensic Dossier
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
            Executive Investigation Report
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Case: <strong>{report.case_name}</strong> • Generated: {new Date(report.generated_at).toLocaleString()}
          </p>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center space-x-2">
          <button disabled={generating} onClick={generate} className="px-3 py-2 bg-blue-600 text-white rounded-lg text-xs">{generating ? 'Generating…' : 'Generate Report'}</button>
          <button onClick={() => setActiveTab('preview')} className="px-3 py-2 border rounded-lg text-xs">Preview Report</button>
          <a href={api.getReportDownloadUrl(report.case_id, 'pdf')} className="px-3 py-2 border rounded-lg text-xs text-blue-700" download>Download PDF</a>
          <a
            href={api.getReportDownloadUrl(report.case_id, 'markdown')}
            download
            className="flex items-center space-x-1.5 px-3.5 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Markdown</span>
          </a>

          <a
            href={api.getReportDownloadUrl(report.case_id, 'json')}
            download
            className="flex items-center space-x-1.5 px-3.5 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition shadow-sm"
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>JSON</span>
          </a>

          <a
            href={api.getReportDownloadUrl(report.case_id, 'html')}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition shadow-sm"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print View</span>
          </a>
        </div>
      </div>

      {/* Provenance Verification Badge */}
      <div className="case-card p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs shadow-sm">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-700" />
          <span className="font-semibold text-emerald-900">
            Source provenance: inspect citations and originals; semantic support requires review
          </span>
        </div>
        <span className="font-mono text-emerald-800 text-[11px] font-medium">
          {report.source_references.length} Source References Available
        </span>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 text-xs border-b border-slate-200">
        <button
          onClick={() => setActiveTab('preview')}
          className={`px-4 py-2 font-semibold transition border-b-2 ${
            activeTab === 'preview'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Dossier View
        </button>
        <button
          onClick={() => setActiveTab('markdown')}
          className={`px-4 py-2 font-semibold transition border-b-2 ${
            activeTab === 'markdown'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Raw Markdown
        </button>
        <button
          onClick={() => setActiveTab('json')}
          className={`px-4 py-2 font-semibold transition border-b-2 ${
            activeTab === 'json'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Structured JSON
        </button>
      </div>

      {/* Tab: Formatted Dossier Preview */}
      {activeTab === 'preview' && (
        <div className="case-card p-6 sm:p-8 rounded-2xl space-y-8 bg-white border border-slate-200/80 shadow-sm">
          {/* Top Dossier Header */}
          <div className="text-center border-b border-slate-200 pb-6">
            <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200 font-mono mb-2 inline-block">
              EXECUTIVE FORENSIC DOSSIER
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mt-2">
              {report.case_name}
            </h2>
            <p className="text-xs text-slate-500 font-mono mt-1">
              Report ID: {report.report_id} • Case ID: {report.case_id}
            </p>
          </div>

          {/* Section 1 & 2: Overview and Documents */}
          <section className="space-y-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2">
              1. Case Overview & Ingested Sources
            </h3>
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
              {report.case_overview}
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                <thead className="bg-slate-50 text-slate-600 font-mono text-[10px] uppercase">
                  <tr>
                    <th className="p-2.5 border-b border-slate-200">Document</th>
                    <th className="p-2.5 border-b border-slate-200">Type</th>
                    <th className="p-2.5 border-b border-slate-200">Speaker / Author</th>
                    <th className="p-2.5 border-b border-slate-200 text-right">Chunks</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {report.documents_analyzed.map((d, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="p-2.5 font-medium text-slate-900">{d.filename}</td>
                      <td className="p-2.5 uppercase text-[10px] text-slate-500 font-mono">{d.document_type}</td>
                      <td className="p-2.5 text-slate-600">{d.speaker || 'Unspecified'}</td>
                      <td className="p-2.5 text-right font-mono font-semibold text-slate-700">{d.chunk_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Section 3: Case conclusion and executive summary */}
          <section className="space-y-2">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2">
              2. Source Claims & Investigation Summary
            </h3>
            <div className="bg-slate-50 p-4 sm:p-5 rounded-xl border border-slate-200/80 text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-line">
              {report.investigation_summary.replace("The system's proposed explanation is", "The highest-ranked evidence claim is")}
              {report.case_summary?.summary.source_span_ids.map(id => <div key={id}><SourceCitation spanId={id} label="Executive-summary source" /></div>)}
            </div>
          </section>

          {/* Section 4 & 5: Proposed Explanation & Formula Breakdown */}
          {report.proposed_explanation && (
            <section className="space-y-3">
              <h3 className="font-bold text-xs uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2 flex items-center justify-between">
                <span>3. Highest-Ranked Evidence Claim</span>
                <span className="text-xs font-mono text-blue-600 font-bold">
                  Evidence-support score: {report.proposed_explanation.evidence_support_score ?? report.proposed_explanation.total_score}
                </span>
              </h3>
              <div className="case-card p-5 rounded-xl border border-blue-500/40 bg-blue-50/20 shadow-sm">
                <div className="flex items-center space-x-2 text-xs font-bold text-blue-700 uppercase tracking-wide">
                  <Award className="w-4 h-4 text-blue-600" />
                  <span>{report.proposed_explanation.title}</span>
                </div>
                {report.proposed_explanation.description !== 'A candidate account drawn from a source passage.' && (
                  <p className="mt-2 text-xs sm:text-sm text-slate-800 leading-relaxed">
                    {report.proposed_explanation.description}
                  </p>
                )}
                <div className="mt-3 text-[11px] font-mono text-slate-500">
                  {report.proposed_explanation.explanation}
                </div>
              </div>
            </section>
          )}

          {report.case_summary && <section className="space-y-3">
            <h3 className="font-bold text-sm">3. Competing hypotheses and score explanations</h3>
            {!report.case_summary.leading_hypothesis && <p className="text-sm text-amber-800">No leading explanation is designated. The evidence remains tied or inadequate.</p>}
            {report.candidate_hypotheses.map(h => <HypothesisCard key={h.hypothesis_id} hypothesis={h} />)}
          </section>}
          {!report.case_summary && !report.proposed_explanation && report.candidate_hypotheses.length > 0 && <section className="space-y-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">3. Hypothesis Scoring — Candidate Source Accounts</h3>
            <p className="text-xs text-slate-600">Scores are uncalibrated ranking heuristics. No account is designated as the actual explanation.</p>
            {report.candidate_hypotheses.map(h => <p key={h.hypothesis_id} className="text-xs border rounded p-3">#{h.rank} · {h.title} · Score: {h.score_method_version ? (h.evidence_support_score ?? 'Not scored') : h.total_score}</p>)}
          </section>}
          {/* Section 6: Contradictions & Conflicts */}
          <section className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                <span>4. Claim Comparisons & Possible Conflicts ({report.contradictions.length})</span>
              </h3>
              <span className="text-[10px] text-slate-400 font-mono">
                Attributed passages, comparison assumptions and human review
              </span>
            </div>

            <div className="space-y-4">
              {report.contradictions.slice(0, 8).map((c, i) => (
                <div key={i} className="p-4 bg-white border border-rose-200/90 rounded-2xl text-xs space-y-3 shadow-sm hover:border-rose-400/80 transition">
                  {/* Card Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
                    <div className="flex items-center space-x-2">
                      <span className="w-5 h-5 rounded-md bg-rose-100 text-rose-800 font-mono font-bold text-[10px] flex items-center justify-center">
                        #{i + 1}
                      </span>
                      <span className="font-bold text-slate-900 text-sm">
                        {c.conflict_title || `Discrepancy: ${c.entity_event_link}`}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      {c.alibi_impact && (
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-50 text-amber-800 border border-amber-200">
                          {c.alibi_impact}
                        </span>
                      )}
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-rose-100 text-rose-800 border border-rose-200">
                        {c.reviewer_id === 'system' && c.review_status === 'confirmed'
                          ? 'Confirmed Contradiction'
                          : c.contradiction_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>

                  {/* Opposing Statements Comparison Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {/* Statement A: Testimonial Claim */}
                    <div className="p-3 bg-amber-50/50 rounded-xl border border-amber-200/80 space-y-1.5">
                      <div className="flex items-center space-x-1.5 text-[11px] font-bold text-amber-900">
                        <User className="w-3.5 h-3.5 text-amber-700" />
                        <span>Source Account A</span>
                      </div>
                      <p className="text-slate-800 italic font-medium bg-white p-2 rounded-lg border border-amber-100 text-xs">
                        "{c.statement_a}"
                      </p>
                      <SourceCitation spanId={c.chunk_a_id} />
                      <div className="text-[10px] text-amber-800/80 font-mono flex items-center justify-between">
                        <span>Source: {c.doc_a_name}</span>
                        <span>Speaker: {c.speaker_a || 'Subject'}</span>
                      </div>
                    </div>

                    {/* Statement B: Objective Rebuttal / Sensor Fact */}
                    <div className="p-3 bg-rose-50/60 rounded-xl border border-rose-200/80 space-y-1.5">
                      <div className="flex items-center space-x-1.5 text-[11px] font-bold text-rose-900">
                        <Cpu className="w-3.5 h-3.5 text-rose-700" />
                        <span>Source Account B</span>
                      </div>
                      <p className="text-slate-800 font-mono bg-white p-2 rounded-lg border border-rose-100 text-xs font-semibold">
                        "{c.statement_b}"
                      </p>
                      <SourceCitation spanId={c.chunk_b_id} />
                      <div className="text-[10px] text-rose-800/80 font-mono flex items-center justify-between">
                        <span>Source: {c.doc_b_name}</span>
                        <span>Attribution: {c.speaker_b || 'Source document'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Forensic Plain-English Explanation */}
                  <div className="p-3 rounded-xl bg-slate-900 text-slate-100 border border-slate-800 space-y-1.5">
                    <div className="flex items-center space-x-1.5 text-[11px] font-bold text-blue-300">
                      <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                      <span>Evidence Comparison & Uncertainty</span>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed font-normal">
                      {c.forensic_analysis || c.explanation}
                    </p>
                    <div className="pt-1 flex items-center justify-between text-[10px] font-mono text-slate-400 border-t border-slate-800">
                      <span>{c.outcome ? `${c.outcome} · ${c.review_action || 'pending human review'}` : 'Legacy comparison; human review required'}</span>
                      <span>Category: {c.evidentiary_category || 'Cross-Document Conflict'}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Section 7: Unresolved Questions */}
          <section className="space-y-2">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2">
              5. Unresolved Questions & Follow-Up Leads
            </h3>
            <ul className="space-y-2 text-xs sm:text-sm text-slate-700 list-disc list-inside">
              {report.unresolved_questions.map((q, i) => (
                <li key={i} className="leading-relaxed">{q}</li>
              ))}
            </ul>
          </section>

          {report.case_summary && <section className="space-y-3">
            <h3 className="font-bold text-sm">Detailed chronological timeline</h3>
            <p className="text-xs text-slate-500">Reported event times are separate from record times; uncertain events remain unordered.</p>
            {report.chronological_timeline.map(event => <article key={event.event_id} className="border rounded-lg p-3 text-sm space-y-1">
              <p className="font-semibold">{event.timestamp_display}</p><p>{event.event_description}</p>
              <p className="text-xs text-slate-500">{event.event_basis} · {event.ordering_group} · record time: {event.record_time || 'unknown'}{event.event_end ? ` · interval end: ${event.event_end}` : ''}</p>
              {(event.source_span_ids || [event.chunk_id || '']).map(id => <div key={id}><SourceCitation spanId={id} /></div>)}
            </article>)}
          </section>}
          {report.graph_snapshot && <section className="space-y-3">
            <h3 className="font-bold text-sm">Relevant entity relationships</h3>
            <p className="text-xs">{report.graph_snapshot.nodes.length} nodes and {report.graph_snapshot.edges.length} sourced relationships. The PDF includes a graph snapshot. <Link to="/graph" className="text-blue-700 underline">Explore the interactive graph</Link></p>
            <details><summary className="cursor-pointer text-xs font-semibold">Inspect relationship evidence</summary>{report.graph_snapshot.edges.map(edge => <div key={edge.id} className="border-t p-2 text-xs">
              <p>{report.graph_snapshot!.nodes.find(n => n.id === edge.source)?.label} → {edge.relation.replace(/_/g, ' ')} → {report.graph_snapshot!.nodes.find(n => n.id === edge.target)?.label}</p>
              {edge.source_span_ids?.map(id => <div key={id}><SourceCitation spanId={id} /></div>)}
            </div>)}</details>
          </section>}
          {/* Section 8: Source References Citations */}
          <section className="space-y-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2 flex items-center justify-between">
              <span>6. Traceable Source References ({report.source_references.length})</span>
              <span className="text-[10px] text-slate-400 font-mono">Click excerpt to inspect provenance details</span>
            </h3>
            <div className="max-h-64 overflow-y-auto space-y-2 pr-2 font-mono text-[10px]">
              {report.source_references.map((ref, i) => (
                <div
                  key={i}
                  onClick={() => setSelectedCitation(ref)}
                  className="p-2.5 bg-slate-50 hover:bg-blue-50 cursor-pointer rounded-lg border border-slate-200 hover:border-blue-400 transition flex items-start justify-between"
                  title="Click to inspect verified source passage"
                  role="button"
                  tabIndex={0}
                >
                  <div className="truncate max-w-lg">
                    <strong className="text-slate-900">[{ref.document}]</strong> {ref.excerpt}
                    <div><SourceCitation spanId={ref.chunk_id} /></div>
                  </div>
                  <span className="text-slate-500 shrink-0 ml-2 font-mono">
                    Sentences: {ref.sentence_indices.join(', ')}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {report.llm_narrative?.sections.map((section, i) => <section className="space-y-2" key={i}>
            <h3 className="font-bold text-sm">{section.title}</h3>
            {section.assertions.map((assertion, j) => <div key={j} className="text-sm"><p>{assertion.kind}: {assertion.text}</p>{assertion.source_span_ids.map(id => <div key={id}><SourceCitation spanId={id} /></div>)}</div>)}
            {section.unknowns.map((unknown, j) => <p key={j} className="text-xs text-amber-800">Unknown: {unknown}</p>)}
          </section>)}
          {/* Section 9: Limitations & Disclaimer */}
          <section className="pt-4 border-t border-slate-200 text-xs text-slate-500 font-mono">
            <pre className="whitespace-pre-wrap bg-slate-50 p-4 rounded-xl border border-slate-200 text-[11px] text-slate-600 leading-relaxed">
              {report.limitations_and_uncertainty}
            </pre>
          </section>
        </div>
      )}

      {/* Tab: Raw Markdown View */}
      {activeTab === 'markdown' && (
        <div className="case-card p-5 rounded-2xl bg-white space-y-3 border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 pb-2 border-b border-slate-100">
            <span>Direct Markdown representation of the 18-section investigation report:</span>
            <button
              onClick={copyMarkdown}
              className="flex items-center space-x-1.5 px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-mono font-semibold transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
            </button>
          </div>
          <textarea
            readOnly
            value={markdownText || 'Loading markdown representation...'}
            className="w-full h-96 p-3.5 font-mono text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-800 leading-relaxed focus:outline-none"
          />
        </div>
      )}

      {/* Tab: JSON View */}
      {activeTab === 'json' && (
        <div className="case-card p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm">
          <pre className="w-full h-96 p-3.5 font-mono text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-800 overflow-auto">
            {JSON.stringify(report, null, 2)}
          </pre>
        </div>
      )}

      {/* Citation Inspector Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-blue-600" />
                <h4 className="font-bold text-sm text-slate-900">
                  Verified Evidence Citation
                </h4>
              </div>
              <button
                onClick={() => setSelectedCitation(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-500 font-mono text-[10px] uppercase">Document:</span>
                <div className="font-bold text-slate-900 mt-0.5">{selectedCitation.document}</div>
              </div>

              <div>
                <span className="text-slate-500 font-mono text-[10px] uppercase">Exact Source Excerpt:</span>
                <div className="p-3 bg-blue-50/60 border border-blue-200 rounded-xl italic text-slate-800 mt-1 leading-relaxed">
                  "{selectedCitation.excerpt}"
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div>Sentence Indices: <strong className="text-slate-800">{selectedCitation.sentence_indices.join(', ')}</strong></div>
                <div>Document ID: <strong className="truncate block text-slate-800">{selectedCitation.document_id || 'Embedded'}</strong></div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedCitation(null)}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
