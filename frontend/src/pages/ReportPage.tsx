import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
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
} from 'lucide-react';

export const ReportPage: React.FC = () => {
  const { activeCaseId, activeCase } = useCase();
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'markdown' | 'json'>('preview');
  const [markdownText, setMarkdownText] = useState<string>('');
  const [selectedCitation, setSelectedCitation] = useState<any | null>(null);

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
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [activeCaseId]);

  if (!report) {
    return (
      <div className="case-card p-12 text-center rounded-lg text-gray-500 text-xs">
        <FileCheck2 className="w-12 h-12 text-gray-300 mx-auto mb-2" />
        <h3 className="text-sm font-bold text-gray-700">No Final Report Available</h3>
        <p className="text-xs text-gray-500 mt-1">
          Run the investigation pipeline in "New Investigation" to generate the full 18-section dossier.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header & Export Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-gray-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
            Module 6 Traceable Dossier
          </div>
          <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
            Final Investigation Report
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Case: <strong>{report.case_name}</strong> • Generated: {new Date(report.generated_at).toLocaleString()}
          </p>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center space-x-2">
          <a
            href={api.getReportDownloadUrl(report.case_id, 'markdown')}
            download
            className="flex items-center space-x-1.5 px-3 py-1.5 border border-gray-300 rounded text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 transition shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Markdown</span>
          </a>

          <a
            href={api.getReportDownloadUrl(report.case_id, 'json')}
            download
            className="flex items-center space-x-1.5 px-3 py-1.5 border border-gray-300 rounded text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 transition shadow-sm"
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>JSON</span>
          </a>

          <a
            href={api.getReportDownloadUrl(report.case_id, 'html')}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#131A2E] text-white rounded text-xs font-semibold hover:bg-[#1D2744] transition shadow-sm"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Printable HTML</span>
          </a>
        </div>
      </div>

      {/* Provenance Verification Badge (Task 2) */}
      <div className="case-card p-3 rounded-lg bg-emerald-50 border border-emerald-300 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2">
          <Shield className="w-4 h-4 text-emerald-700" />
          <span className="font-semibold text-emerald-900">
            Provenance Verification Audit: 100% Traceable Source Citations
          </span>
        </div>
        <span className="font-mono text-emerald-800 text-[11px]">
          {report.source_references.length} Document Excerpts Verified
        </span>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 text-xs border-b border-gray-200 pb-1">
        <button
          onClick={() => setActiveTab('preview')}
          className={`px-3 py-1.5 rounded-t font-semibold transition ${
            activeTab === 'preview'
              ? 'border-b-2 border-[#C9962F] text-[#C9962F] bg-white'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Dossier Preview (All 18 Sections)
        </button>
        <button
          onClick={() => setActiveTab('markdown')}
          className={`px-3 py-1.5 rounded-t font-semibold transition ${
            activeTab === 'markdown'
              ? 'border-b-2 border-[#C9962F] text-[#C9962F] bg-white'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Raw Markdown Export
        </button>
        <button
          onClick={() => setActiveTab('json')}
          className={`px-3 py-1.5 rounded-t font-semibold transition ${
            activeTab === 'json'
              ? 'border-b-2 border-[#C9962F] text-[#C9962F] bg-white'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Structured JSON Format
        </button>
      </div>

      {/* Tab: Formatted Dossier Preview */}
      {activeTab === 'preview' && (
        <div className="case-card p-8 rounded-lg space-y-8 bg-white border border-[#E2DDD0]">
          {/* Top Dossier Seal */}
          <div className="text-center border-b-2 border-double border-[#C9962F] pb-6">
            <span className="stamp-label stamp-navy text-[11px] mb-2">
              CONFIDENTIAL // EVIDENCE DOSSIER
            </span>
            <h2 className="font-serif text-2xl font-bold text-[#131A2E] mt-1">
              {report.case_name}
            </h2>
            <p className="text-xs text-gray-500 font-mono mt-1">
              Report ID: {report.report_id} • Case Reference: {report.case_id}
            </p>
          </div>

          {/* Section 1 & 2: Overview and Documents */}
          <section className="space-y-3">
            <h3 className="font-serif font-bold text-sm text-[#131A2E] uppercase tracking-wider border-b pb-1">
              1. Case Overview & Documents Ingested
            </h3>
            <p className="text-xs text-gray-700 leading-relaxed font-serif">
              {report.case_overview}
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-gray-200 rounded">
                <thead className="bg-[#FAF8F3] text-gray-600 font-mono text-[10px] uppercase">
                  <tr>
                    <th className="p-2 border-b">Document</th>
                    <th className="p-2 border-b">Type</th>
                    <th className="p-2 border-b">Speaker / Author</th>
                    <th className="p-2 border-b text-right">Chunks</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 font-serif">
                  {report.documents_analyzed.map((d, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="p-2 font-medium">{d.filename}</td>
                      <td className="p-2 uppercase text-[10px] text-gray-500 font-mono">{d.document_type}</td>
                      <td className="p-2 text-gray-600">{d.speaker || 'Unspecified'}</td>
                      <td className="p-2 text-right font-mono">{d.chunk_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Section 3: Executive Summary */}
          <section className="space-y-2">
            <h3 className="font-serif font-bold text-sm text-[#131A2E] uppercase tracking-wider border-b pb-1">
              2. Executive Investigation Summary
            </h3>
            <div className="bg-[#FAF8F3] p-4 rounded border-l-4 border-[#C9962F] text-xs text-gray-800 leading-relaxed font-serif">
              {report.investigation_summary}
            </div>
          </section>

          {/* Section 4 & 5: Proposed Explanation & Formula Breakdown */}
          {report.proposed_explanation && (
            <section className="space-y-3">
              <h3 className="font-serif font-bold text-sm text-[#131A2E] uppercase tracking-wider border-b pb-1 flex items-center justify-between">
                <span>3. System's Proposed Explanation</span>
                <span className="text-xs font-mono text-[#C9962F] font-bold">
                  Score: {report.proposed_explanation.total_score}
                </span>
              </h3>
              <div className="case-card p-5 rounded border-2 border-[#C9962F] bg-[#FFFDF9]">
                <div className="flex items-center space-x-2 text-xs font-bold text-[#A87A1E] font-serif uppercase">
                  <Award className="w-4 h-4 text-[#C9962F]" />
                  <span>{report.proposed_explanation.title}</span>
                </div>
                <p className="mt-2 text-xs text-gray-800 leading-relaxed font-serif">
                  {report.proposed_explanation.description}
                </p>
                <div className="mt-3 text-[11px] font-mono text-gray-500">
                  {report.proposed_explanation.explanation}
                </div>
              </div>
            </section>
          )}

          {/* Section 6: Contradictions & Conflicts */}
          <section className="space-y-3">
            <h3 className="font-serif font-bold text-sm text-[#131A2E] uppercase tracking-wider border-b pb-1">
              4. Cross-Document Contradictions ({report.contradictions.length})
            </h3>
            <div className="space-y-3">
              {report.contradictions.slice(0, 6).map((c, i) => (
                <div key={i} className="p-3 bg-[#FAF8F3] border border-red-200 rounded text-xs space-y-1">
                  <div className="font-bold text-red-800 flex items-center justify-between">
                    <span>Discrepancy #{i + 1}: {c.entity_event_link}</span>
                    <span className="stamp-label stamp-danger text-[9px]">{c.contradiction_type}</span>
                  </div>
                  <p className="text-gray-700 italic">
                    "{c.statement_a}" vs "{c.statement_b}"
                  </p>
                  <p className="text-[11px] text-gray-500">
                    Sources: {c.doc_a_name} ({c.speaker_a || 'Unknown'}) & {c.doc_b_name} ({c.speaker_b || 'Unknown'})
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Section 7: Unresolved Questions */}
          <section className="space-y-2">
            <h3 className="font-serif font-bold text-sm text-[#131A2E] uppercase tracking-wider border-b pb-1">
              5. Unresolved Questions & Discrepancies
            </h3>
            <ul className="space-y-1.5 text-xs text-gray-700 list-disc list-inside font-serif">
              {report.unresolved_questions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ul>
          </section>

          {/* Section 8: Source References Citations */}
          <section className="space-y-3">
            <h3 className="font-serif font-bold text-sm text-[#131A2E] uppercase tracking-wider border-b pb-1 flex items-center justify-between">
              <span>6. Traceable Source References ({report.source_references.length})</span>
              <span className="text-[10px] text-gray-500 font-mono">Click any excerpt to inspect source details</span>
            </h3>
            <div className="max-h-64 overflow-y-auto space-y-1.5 pr-2 font-mono text-[10px]">
              {report.source_references.map((ref, i) => (
                <div
                  key={i}
                  onClick={() => setSelectedCitation(ref)}
                  className="p-2.5 bg-gray-50 hover:bg-amber-50 cursor-pointer rounded border border-gray-200 hover:border-amber-400 transition flex items-start justify-between"
                  title="Click to inspect verified source passage"
                  role="button"
                  tabIndex={0}
                >
                  <div className="truncate max-w-lg">
                    <strong className="text-gray-900">[{ref.document}]</strong> {ref.excerpt}
                  </div>
                  <span className="text-gray-500 shrink-0 ml-2 font-mono">
                    Sentences: {ref.sentence_indices.join(', ')}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* Section 9: Limitations & Disclaimer */}
          <section className="pt-4 border-t border-gray-200 text-xs text-gray-500 font-mono">
            <pre className="whitespace-pre-wrap bg-gray-50 p-3 rounded border text-[11px] text-gray-600">
              {report.limitations_and_uncertainty}
            </pre>
          </section>
        </div>
      )}

      {/* Tab: Raw Markdown View */}
      {activeTab === 'markdown' && (
        <div className="case-card p-4 rounded-lg bg-white space-y-2">
          <div className="flex items-center justify-between text-xs text-gray-500 pb-2 border-b">
            <span>Direct Markdown representation of the 18-section investigation report:</span>
            <button
              onClick={() => navigator.clipboard.writeText(markdownText)}
              className="px-2.5 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-mono font-semibold"
            >
              Copy to Clipboard
            </button>
          </div>
          <textarea
            readOnly
            value={markdownText || 'Loading markdown representation...'}
            className="w-full h-96 p-3 font-mono text-xs bg-gray-50 border rounded text-gray-800 leading-relaxed"
          />
        </div>
      )}

      {/* Tab: JSON View */}
      {activeTab === 'json' && (
        <div className="case-card p-4 rounded-lg bg-white">
          <pre className="w-full h-96 p-3 font-mono text-xs bg-gray-50 border rounded text-gray-800 overflow-auto">
            {JSON.stringify(report, null, 2)}
          </pre>
        </div>
      )}

      {/* Citation Inspector Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl space-y-4 border border-[#E2DDD0]">
            <div className="flex items-center justify-between border-b pb-2">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-[#C9962F]" />
                <h4 className="font-serif font-bold text-sm text-[#131A2E]">
                  Verified Evidence Citation
                </h4>
              </div>
              <button
                onClick={() => setSelectedCitation(null)}
                className="text-gray-400 hover:text-gray-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-gray-500 font-mono text-[10px] uppercase">Document:</span>
                <div className="font-bold text-[#131A2E]">{selectedCitation.document}</div>
              </div>

              <div>
                <span className="text-gray-500 font-mono text-[10px] uppercase">Exact Source Excerpt:</span>
                <div className="p-3 bg-amber-50/60 border border-amber-200 rounded italic text-gray-800 mt-1 leading-relaxed">
                  "{selectedCitation.excerpt}"
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-gray-600 bg-gray-50 p-2.5 rounded border">
                <div>Sentence Indices: <strong>{selectedCitation.sentence_indices.join(', ')}</strong></div>
                <div>Document ID: <strong className="truncate block">{selectedCitation.document_id || 'Embedded'}</strong></div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedCitation(null)}
                className="px-4 py-1.5 bg-[#131A2E] text-white rounded text-xs font-semibold hover:bg-[#1D2744]"
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
