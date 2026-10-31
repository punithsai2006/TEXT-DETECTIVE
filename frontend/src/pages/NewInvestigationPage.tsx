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
    { num: 1, name: 'Ingestion & Preprocessing', pct: 15 },
    { num: 2, name: 'Entity, Event & Time Extraction', pct: 35 },
    { num: 3, name: 'RAG Evidence Retrieval & Indexing', pct: 50 },
    { num: 4, name: 'Contradiction & Linking Agent', pct: 65 },
    { num: 5, name: 'Hypothesis Scoring & Ranking', pct: 80 },
    { num: 6, name: 'Source-Linked Report Generation', pct: 100 },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Title */}
      <div className="border-b border-gray-200 pb-4">
        <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
          Workflow Pipeline
        </div>
        <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
          Document Ingestion & Automated Investigation
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Upload heterogeneous files (interviews, emails, reports, logs) and trigger the 6-module agentic pipeline.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Case Header selector */}
      <div className="case-card p-4 rounded-lg flex items-center justify-between">
        <div>
          <span className="text-[11px] text-gray-500 font-semibold uppercase">Target Investigation:</span>
          <h3 className="font-serif font-bold text-base text-[#131A2E]">
            {activeCase?.name || 'No Case Selected'}
          </h3>
        </div>

        <button
          onClick={() => navigate('/cases')}
          className="text-xs text-[#C9962F] hover:underline font-medium flex items-center"
        >
          <FolderOpen className="w-3.5 h-3.5 mr-1" />
          <span>Switch Case</span>
        </button>
      </div>

      {/* Upload Dropzone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleFileDrop}
        className="border-2 border-dashed border-[#C9962F]/60 rounded-xl p-8 text-center bg-[#FAF8F3] hover:bg-[#F4F0E6]/50 transition cursor-pointer"
      >
        <UploadCloud className="w-12 h-12 text-[#C9962F] mx-auto mb-2" />
        <h3 className="text-sm font-bold text-[#131A2E] font-serif">
          Drag and Drop Case Files Here
        </h3>
        <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
          Supports <strong>TXT, PDF, DOCX, CSV, JSON, and LOG</strong> files. Each chunk will retain exact sentence references.
        </p>

        <label className="mt-4 inline-block px-4 py-2 bg-[#131A2E] text-white text-xs font-semibold rounded cursor-pointer hover:bg-[#1D2744] transition shadow">
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
        <div className="case-card p-4 rounded-lg space-y-3">
          <div className="flex items-center justify-between border-b pb-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-700">
              Files in Staging Queue ({filesToUpload.length})
            </h4>
            <button
              onClick={() => setFilesToUpload([])}
              className="text-xs text-red-600 hover:underline"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            {filesToUpload.map((f, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-2 bg-[#FAF8F3] rounded text-xs border border-gray-100"
              >
                <div className="flex items-center space-x-2 truncate">
                  <FileText className="w-4 h-4 text-[#C9962F] shrink-0" />
                  <span className="font-semibold text-gray-800 truncate">{f.name}</span>
                  <span className="text-[10px] text-gray-400 font-mono">
                    ({(f.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  onClick={() => removeFile(i)}
                  className="p-1 text-gray-400 hover:text-red-600"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>

          {/* Optional Metadata Tags */}
          <div className="pt-3 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-[11px] font-semibold text-gray-600 mb-1">
                Document Type (Optional Override)
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full p-1.5 border border-gray-300 rounded text-xs"
              >
                <option value="other">Auto-detect from content</option>
                <option value="interview">Witness Interview</option>
                <option value="email">Email / Memo</option>
                <option value="report">Incident / Forensic Report</option>
                <option value="log">Access / Badge Log</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-gray-600 mb-1">
                Speaker / Author (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Alice Vance"
                value={speaker}
                onChange={(e) => setSpeaker(e.target.value)}
                className="w-full p-1.5 border border-gray-300 rounded text-xs"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-gray-600 mb-1">
                Timestamp (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. 2024-10-12 22:15"
                value={timestamp}
                onChange={(e) => setTimestamp(e.target.value)}
                className="w-full p-1.5 border border-gray-300 rounded text-xs"
              />
            </div>
          </div>
        </div>
      )}

      {/* Launch Investigation Button */}
      <div className="flex items-center justify-between pt-2">
        <span className="text-xs text-gray-500">
          Already has <strong>{activeCase?.document_count || 0}</strong> uploaded files in archive.
        </span>

        <button
          onClick={handleUploadAndAnalyze}
          disabled={uploading || analyzing}
          className="flex items-center space-x-2 px-6 py-2.5 bg-[#C9962F] text-[#131A2E] text-xs font-bold rounded-lg hover:bg-[#E0B354] transition shadow-md disabled:opacity-50"
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
              <span>Run Investigation Pipeline</span>
            </>
          )}
        </button>
      </div>

      {/* Progress & Feedback Loops Display */}
      {(analyzing || status) && (
        <div className="case-card p-5 rounded-lg border-2 border-[#131A2E] space-y-4">
          <div className="flex items-center justify-between border-b pb-2">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-[#C9962F]" />
              <h3 className="font-serif font-bold text-sm text-[#131A2E]">
                Pipeline Execution Tracker
              </h3>
            </div>
            <span className="text-xs font-bold font-mono text-[#C9962F]">
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
                <div key={s.num} className="flex items-center justify-between text-xs p-2 rounded bg-[#FAF8F3]">
                  <div className="flex items-center space-x-2">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] ${
                      isDone ? 'bg-emerald-600 text-white' : 'bg-gray-200 text-gray-600'
                    }`}>
                      {isDone ? '✓' : s.num}
                    </span>
                    <span className={`font-semibold ${isDone ? 'text-gray-900' : 'text-gray-500'}`}>
                      {s.name}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-gray-400">
                    {isDone ? 'COMPLETED' : isCurrent ? 'RUNNING...' : 'PENDING'}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Feedback Loops Log */}
          {status?.feedback_loops && status.feedback_loops.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-200">
              <h4 className="text-xs font-bold uppercase tracking-wider text-purple-900 mb-2">
                Controller Feedback Loops Triggered:
              </h4>
              <div className="space-y-1.5 text-xs">
                {status.feedback_loops.map((loop, idx) => (
                  <div key={idx} className="bg-purple-50 border border-purple-200 p-2.5 rounded text-purple-900">
                    <div className="font-bold flex items-center justify-between">
                      <span>{loop.loop_name} (Iteration {loop.iteration}/2)</span>
                      <span className="text-[10px] font-mono text-purple-700">
                        {new Date(loop.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-purple-800">
                      <strong>Trigger:</strong> {loop.trigger_reason}
                    </p>
                    <p className="text-[11px] text-purple-800">
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
                className="px-4 py-2 bg-emerald-700 text-white font-bold text-xs rounded hover:bg-emerald-800 transition flex items-center"
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
