import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { DocumentType, AnalysisStatus } from '../types';
import {
  UploadCloud,
  FileText,
  Trash2,
  Play,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  FolderOpen,
  ArrowRight,
  Sparkles,
  Layers,
  Repeat,
} from 'lucide-react';

export const NewInvestigationPage: React.FC = () => {
  const { cases, activeCaseId, activeCase, setActiveCaseId, refreshCases } = useCase();
  const navigate = useNavigate();

  const [filesToUpload, setFilesToUpload] = useState<File[]>([]);
  const [docType, setDocType] = useState<string>('other');
  const [speaker, setSpeaker] = useState('');
  const [author, setAuthor] = useState('');
  const [timestamp, setTimestamp] = useState('');
  const [description, setDescription] = useState('');

  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles: File[]) => {
    const valid = newFiles.filter((f) => {
      const ext = f.name.toLowerCase().split('.').pop();
      return ['txt', 'pdf', 'docx', 'csv', 'json', 'log', 'md'].includes(ext || '');
    });
    setFilesToUpload((prev) => [...prev, ...valid]);
  };

  const removeFile = (idx: number) => {
    setFilesToUpload((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleUploadAndAnalyze = async () => {
    if (!activeCaseId) {
      setError('Please select or create an active case first.');
      return;
    }
    if (filesToUpload.length === 0 && (activeCase?.document_count || 0) === 0) {
      setError('Please select at least one document to upload.');
      return;
    }

    setError(null);
    setUploading(true);

    try {
      if (filesToUpload.length > 0) {
        const formData = new FormData();
        filesToUpload.forEach((f) => formData.append('files', f));
        if (docType && docType !== 'other') formData.append('document_type', docType);
        if (speaker) formData.append('speaker', speaker);
        if (author) formData.append('author', author);
        if (timestamp) formData.append('timestamp', timestamp);
        if (description) formData.append('description', description);

        await api.uploadDocuments(activeCaseId, formData);
        setFilesToUpload([]);
      }

      setUploading(false);
      setAnalyzing(true);

      // Run full controller pipeline
      const report = await api.runAnalysis(activeCaseId);
      await refreshCases();

      const finalStatus = await api.getAnalysisStatus(activeCaseId);
      setStatus(finalStatus);
    } catch (err: any) {
      setError(err.message || 'Investigation execution failed.');
    } finally {
      setUploading(false);
      setAnalyzing(false);
    }
  };

  const moduleSteps = [
    { num: 1, name: 'Ingestion & Sentence Parsing', pct: 15 },
    { num: 2, name: 'Entity & Event Reconstruction', pct: 35 },
    { num: 3, name: 'RAG Hybrid Evidence Indexing', pct: 50 },
    { num: 4, name: 'Cross-Document Contradiction Engine', pct: 65 },
    { num: 5, name: 'Slide 18 Hypothesis Scoring', pct: 80 },
    { num: 6, name: 'Audit Dossier Generation', pct: 100 },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div className="border-b border-slate-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
          Workflow Pipeline Orchestrator
        </div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
          Document Ingestion & Automated Investigation
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          Upload heterogeneous files (interviews, emails, reports, logs) and trigger the 6-module agentic pipeline.
        </p>
      </div>

      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center shadow-sm">
          <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Target Case Banner */}
      <div className="case-card p-4 sm:p-5 rounded-2xl flex items-center justify-between shadow-sm border border-slate-200/80">
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Target Investigation Dossier:</span>
          <h3 className="font-bold text-base sm:text-lg text-slate-900 mt-0.5">
            {activeCase?.name || 'No Case Selected'}
          </h3>
        </div>

        <button
          onClick={() => navigate('/cases')}
          className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center px-3 py-1.5 rounded-lg hover:bg-blue-50 transition"
        >
          <FolderOpen className="w-4 h-4 mr-1.5" />
          <span>Switch Case</span>
        </button>
      </div>

      {/* Upload Dropzone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleFileDrop}
        className="border-2 border-dashed border-blue-400/70 rounded-2xl p-8 sm:p-10 text-center bg-blue-50/20 hover:bg-blue-50/40 transition-all cursor-pointer"
      >
        <UploadCloud className="w-12 h-12 text-blue-600 mx-auto mb-2" />
        <h3 className="text-base font-bold text-slate-900">
          Drag and Drop Case Files Here
        </h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto leading-relaxed">
          Supports <strong>TXT, PDF, DOCX, CSV, JSON, and LOG</strong> files. Extracted sentences retain strict offsets and IDs.
        </p>

        <label className="mt-4 inline-block px-4 py-2 bg-slate-900 text-white text-xs font-semibold rounded-xl cursor-pointer hover:bg-slate-800 transition shadow-sm">
          <span>Browse Files</span>
          <input
            type="file"
            multiple
            accept=".txt,.pdf,.docx,.csv,.json,.log,.md"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>
      </div>

      {/* Selected Files Queue */}
      {filesToUpload.length > 0 && (
        <div className="case-card p-5 rounded-2xl space-y-4 shadow-sm border border-slate-200/80">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Files in Staging Queue ({filesToUpload.length})
            </h4>
            <button
              onClick={() => setFilesToUpload([])}
              className="text-xs text-rose-600 hover:underline font-semibold"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {filesToUpload.map((f, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl text-xs border border-slate-200/60"
              >
                <div className="flex items-center space-x-2.5 truncate">
                  <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                  <span className="font-semibold text-slate-800 truncate">{f.name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    ({(f.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  onClick={() => removeFile(i)}
                  className="p-1 text-slate-400 hover:text-rose-600 rounded transition"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>

          {/* Optional Metadata Tags */}
          <div className="pt-3 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                Document Type Override (Optional)
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="other">Auto-detect from content</option>
                <option value="interview">Witness Interview</option>
                <option value="email">Email / Memo</option>
                <option value="report">Incident / Police Report</option>
                <option value="log">Access / Badge Log</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                Speaker / Author (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Alice Vance"
                value={speaker}
                onChange={(e) => setSpeaker(e.target.value)}
                className="w-full p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                Timestamp (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. 2024-10-12 22:15"
                value={timestamp}
                onChange={(e) => setTimestamp(e.target.value)}
                className="w-full p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>
        </div>
      )}

      {/* Launch Investigation Button */}
      <div className="flex items-center justify-between pt-2 flex-wrap gap-3">
        <span className="text-xs text-slate-500">
          Already has <strong>{activeCase?.document_count || 0}</strong> uploaded files in archive.
        </span>

        <button
          onClick={handleUploadAndAnalyze}
          disabled={uploading || analyzing}
          className="flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-xs font-semibold rounded-xl transition shadow-sm disabled:opacity-50"
        >
          {uploading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Uploading Files...</span>
            </>
          ) : analyzing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Executing Controller Pipeline...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run Full Investigation Pipeline</span>
            </>
          )}
        </button>
      </div>

      {/* Progress & Feedback Loops Display */}
      {(analyzing || status) && (
        <div className="case-card p-6 rounded-2xl border border-slate-200/80 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <h3 className="font-bold text-sm text-slate-900">
                Pipeline Execution Status
              </h3>
            </div>
            <span className="text-xs font-bold font-mono text-blue-600 uppercase bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
              {status?.status?.toUpperCase() || (analyzing ? 'PROCESSING' : 'DONE')}
            </span>
          </div>

          {/* Module Step Indicator */}
          <div className="space-y-2">
            {moduleSteps.map((s) => {
              const currentProgress = status?.progress_percentage || (analyzing ? 45 : 100);
              const isDone = currentProgress >= s.pct;
              const isCurrent = currentProgress >= s.pct - 20 && currentProgress < s.pct;

              return (
                <div key={s.num} className="flex items-center justify-between text-xs p-2.5 rounded-xl bg-slate-50 border border-slate-200/60">
                  <div className="flex items-center space-x-2.5">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] ${
                      isDone ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
                    }`}>
                      {isDone ? '✓' : s.num}
                    </span>
                    <span className={`font-semibold ${isDone ? 'text-slate-900' : 'text-slate-500'}`}>
                      {s.name}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">
                    {isDone ? 'COMPLETED' : isCurrent ? 'RUNNING...' : 'PENDING'}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Feedback Loops Log */}
          {status?.feedback_loops && status.feedback_loops.length > 0 && (
            <div className="mt-4 pt-3 border-t border-slate-100">
              <h4 className="text-xs font-bold uppercase tracking-wider text-purple-900 mb-2.5 flex items-center gap-1.5">
                <Repeat className="w-3.5 h-3.5 text-purple-600" />
                <span>Controller Feedback Loops Triggered:</span>
              </h4>
              <div className="space-y-2 text-xs">
                {status.feedback_loops.map((loop, idx) => (
                  <div key={idx} className="bg-purple-50/70 border border-purple-200/80 p-3 rounded-xl text-purple-950">
                    <div className="font-bold flex items-center justify-between">
                      <span>{loop.loop_name} (Iteration {loop.iteration}/2)</span>
                      <span className="text-[10px] font-mono text-purple-700">
                        {new Date(loop.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-purple-900">
                      <strong>Trigger:</strong> {loop.trigger_reason}
                    </p>
                    <p className="text-[11px] text-purple-900">
                      <strong>Action:</strong> {loop.action_taken}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigate to Report Button */}
          {!analyzing && status?.status === 'completed' && (
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => navigate('/report')}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-xl transition flex items-center shadow-sm"
              >
                <span>View Full Investigation Dossier</span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
