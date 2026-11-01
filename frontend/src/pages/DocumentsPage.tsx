import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { DocumentMetadata, DocumentType, TextChunk } from '../types';
import {
  FileText,
  User,
  Clock,
  Trash2,
  ChevronRight,
  AlertCircle,
  FolderOpen,
  Search,
  Filter,
  Layers,
  Copy,
  Check,
  PlusCircle,
  UploadCloud,
  RefreshCw,
  FileCode,
} from 'lucide-react';

export const DocumentsPage: React.FC = () => {
  const { activeCaseId, activeCase, refreshCases } = useCase();
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [copiedChunkId, setCopiedChunkId] = useState<string | null>(null);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploadDocType, setUploadDocType] = useState('other');
  const [uploadSpeaker, setUploadSpeaker] = useState('');
  const [uploadTimestamp, setUploadTimestamp] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fetchDocs = () => {
    if (!activeCaseId) return;
    setLoading(true);
    api
      .getCaseDocuments(activeCaseId)
      .then((docs) => {
        setDocuments(docs);
        if (docs.length > 0 && !selectedDoc) {
          setSelectedDoc(docs[0]);
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDocs();
  }, [activeCaseId]);

  const handleDelete = async (docId: string, filename: string) => {
    if (!activeCaseId) return;
    if (!window.confirm(`Delete document '${filename}'? This will permanently remove the file, extracted chunks, and mark the analysis as outdated.`)) return;
    try {
      await api.deleteCaseDocument(activeCaseId, docId);
      await refreshCases();
      setDocuments((prev) => prev.filter((d) => d.document_id !== docId));
      if (selectedDoc?.document_id === docId) {
        setSelectedDoc(null);
      }
    } catch (e: any) {
      alert(`Delete failed: ${e.message}`);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCaseId || uploadFiles.length === 0) return;
    setUploading(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      uploadFiles.forEach((f) => formData.append('files', f));
      if (uploadDocType && uploadDocType !== 'other') formData.append('document_type', uploadDocType);
      if (uploadSpeaker.trim()) formData.append('speaker', uploadSpeaker.trim());
      if (uploadTimestamp.trim()) formData.append('timestamp', uploadTimestamp.trim());

      await api.uploadDocuments(activeCaseId, formData);
      await refreshCases();
      fetchDocs();
      setShowUploadModal(false);
      setUploadFiles([]);
      setUploadSpeaker('');
      setUploadTimestamp('');
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const copyChunk = (chunk: TextChunk) => {
    navigator.clipboard.writeText(chunk.text);
    setCopiedChunkId(chunk.chunk_id);
    setTimeout(() => setCopiedChunkId(null), 2000);
  };

  const filteredDocs = documents.filter((doc) => {
    if (typeFilter !== 'all' && doc.document_type !== typeFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = doc.filename.toLowerCase().includes(q);
      const matchSpeaker = (doc.speaker || '').toLowerCase().includes(q);
      const matchText = (doc.cleaned_text || doc.raw_text || '').toLowerCase().includes(q);
      if (!matchName && !matchSpeaker && !matchText) return false;
    }
    return true;
  });

  if (!activeCaseId) {
    return (
      <div className="case-card p-12 text-center rounded-2xl">
        <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-800">No Active Case Selected</h3>
        <p className="text-xs text-slate-500 mt-1">Please select an investigation from the top navigation bar.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
            Case Evidence Repository
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
            Documents Explorer
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            <strong>{documents.length}</strong> source files indexed for <strong>{activeCase?.name}</strong>.
          </p>
        </div>

        {/* Action & Filter Controls */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search filename or text..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 w-44 sm:w-52 shadow-sm"
              aria-label="Search document filenames and content"
            />
          </div>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm cursor-pointer"
            aria-label="Filter documents by category"
          >
            <option value="all">All Document Types</option>
            <option value="interview">Witness Interviews</option>
            <option value="email">Emails & Letters</option>
            <option value="report">Incident Reports</option>
            <option value="log">Access Logs</option>
            <option value="other">Other Documents</option>
          </select>

          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition shadow-sm"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Add Files</span>
          </button>
        </div>
      </div>

      {/* Main Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Document List */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 px-1">
            <span>Files ({filteredDocs.length})</span>
            {filteredDocs.length !== documents.length && (
              <span className="text-[10px] text-blue-600 lowercase">(filtered from {documents.length})</span>
            )}
          </div>

          {filteredDocs.map((doc) => {
            const isSelected = selectedDoc?.document_id === doc.document_id;
            return (
              <div
                key={doc.document_id}
                onClick={() => setSelectedDoc(doc)}
                className={`case-card p-3.5 rounded-xl cursor-pointer transition-all flex items-center justify-between ${
                  isSelected
                    ? 'border-blue-500 bg-blue-50/30 ring-1 ring-blue-500 shadow-sm'
                    : 'hover:border-slate-300'
                }`}
                role="button"
                tabIndex={0}
                aria-label={`Select document ${doc.filename}`}
              >
                <div className="flex items-center space-x-3 truncate">
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
                    <FileText className="w-4 h-4 shrink-0" />
                  </div>
                  <div className="truncate text-left">
                    <div className="text-xs font-bold text-slate-900 truncate">
                      {doc.filename}
                    </div>
                    <div className="text-[10px] text-slate-500 flex items-center space-x-2 mt-0.5">
                      <span className="uppercase font-mono text-[9px] px-1.5 py-0.5 bg-slate-100 rounded text-slate-700 font-semibold">
                        {doc.document_type}
                      </span>
                      <span>{doc.chunks.length} chunks</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-1.5 shrink-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(doc.document_id, doc.filename);
                    }}
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                    title="Delete document"
                    aria-label={`Delete ${doc.filename}`}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <ChevronRight className={`w-4 h-4 ${isSelected ? 'text-blue-600' : 'text-slate-300'}`} />
                </div>
              </div>
            );
          })}

          {filteredDocs.length === 0 && (
            <div className="case-card p-8 text-center text-xs text-slate-500 rounded-xl">
              No documents match your query.
            </div>
          )}
        </div>

        {/* Right: Selected Document Detail & Chunks */}
        <div className="lg:col-span-2">
          {selectedDoc ? (
            <div className="case-card p-5 sm:p-6 rounded-2xl space-y-5 shadow-sm">
              {/* Doc Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-slate-900">
                    {selectedDoc.filename}
                  </h2>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-1.5">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-slate-100 text-slate-700 font-mono border border-slate-200">
                      {selectedDoc.document_type}
                    </span>
                    {selectedDoc.speaker && (
                      <span className="flex items-center text-slate-700 font-medium bg-blue-50 px-2 py-0.5 rounded-full text-[11px] border border-blue-100">
                        <User className="w-3 h-3 mr-1 text-blue-600" />
                        Speaker: <strong>{selectedDoc.speaker}</strong>
                      </span>
                    )}
                    {selectedDoc.timestamp && (
                      <span className="flex items-center text-slate-600 font-mono text-[11px]">
                        <Clock className="w-3 h-3 mr-1 text-slate-400" />
                        Time: {selectedDoc.timestamp}
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-right text-[10px] font-mono text-slate-400 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
                  ID: {selectedDoc.document_id}
                </div>
              </div>

              {/* Full Text Preview */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Extracted Document Text
                </h4>
                <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-xs font-mono max-h-52 overflow-y-auto whitespace-pre-wrap text-slate-800 leading-relaxed shadow-inner">
                  {selectedDoc.cleaned_text || selectedDoc.raw_text}
                </div>
              </div>

              {/* Chunks Explorer */}
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-blue-600" />
                    <span>Semantic Chunks ({selectedDoc.chunks.length})</span>
                  </h4>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Sentence-Indexed • Overlap: 80 chars
                  </span>
                </div>

                <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                  {selectedDoc.chunks.map((chunk, idx) => (
                    <div
                      key={chunk.chunk_id}
                      className="bg-white border border-slate-200/80 rounded-xl p-3.5 text-xs hover:border-blue-400 transition-all shadow-sm"
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono mb-1.5">
                        <span className="font-bold text-blue-600">
                          Chunk #{idx + 1} ({chunk.chunk_id})
                        </span>
                        <div className="flex items-center space-x-2">
                          <span>
                            Sentences: [{chunk.sentence_indices.join(', ')}]
                          </span>
                          <button
                            onClick={() => copyChunk(chunk)}
                            className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition"
                            title="Copy chunk text"
                          >
                            {copiedChunkId === chunk.chunk_id ? (
                              <Check className="w-3 h-3 text-emerald-600" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </div>
                      <p className="text-slate-800 leading-relaxed font-normal">
                        {chunk.text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="case-card p-12 text-center rounded-2xl text-slate-400 text-xs">
              Select a document on the left to inspect content and semantic chunks.
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-blue-600" />
                <span>Upload Documents to Case</span>
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition"
              >
                ✕
              </button>
            </div>

            {uploadError && (
              <div className="mt-3 p-2.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center">
                <AlertCircle className="w-4 h-4 mr-1.5 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="mt-4 space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1.5">
                  Choose Files (TXT, PDF, DOCX, CSV, JSON, LOG) *
                </label>
                <input
                  type="file"
                  multiple
                  required
                  accept=".txt,.pdf,.docx,.csv,.json,.log,.md"
                  onChange={(e) => {
                    if (e.target.files) setUploadFiles(Array.from(e.target.files));
                  }}
                  className="w-full p-2 border border-slate-300 rounded-xl text-xs file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Document Type Override (Optional)
                </label>
                <select
                  value={uploadDocType}
                  onChange={(e) => setUploadDocType(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="other">Auto-detect from content</option>
                  <option value="interview">Witness Interview</option>
                  <option value="email">Email / Memo</option>
                  <option value="report">Incident / Police Report</option>
                  <option value="log">Access / Badge Log</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Speaker / Author (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Alice Vance"
                    value={uploadSpeaker}
                    onChange={(e) => setUploadSpeaker(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Timestamp (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 2024-10-12 22:15"
                    value={uploadTimestamp}
                    onChange={(e) => setUploadTimestamp(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-3.5 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || uploadFiles.length === 0}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg transition disabled:opacity-50 shadow-sm flex items-center gap-1.5"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Ingesting...</span>
                    </>
                  ) : (
                    <span>Upload & Ingest</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
