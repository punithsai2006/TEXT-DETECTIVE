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
  AlertTriangle,
  FolderOpen,
  Search,
  Filter,
} from 'lucide-react';

export const DocumentsPage: React.FC = () => {
  const { activeCaseId, activeCase, refreshCases } = useCase();
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
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
      <div className="case-card p-12 text-center rounded-lg">
        <FolderOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <h3 className="text-sm font-bold text-gray-700">No Active Case Selected</h3>
        <p className="text-xs text-gray-500 mt-1">Please select an investigation from the top bar.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
            Evidence Ingestion Files (Module 1)
          </div>
          <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
            Documents Explorer
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Inspected {documents.length} source documents for case <strong>{activeCase?.name}</strong>.
          </p>
        </div>

        {/* Filter and Search Controls */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search filename or text..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-white border border-gray-300 rounded text-xs text-[#131A2E] focus:outline-none focus:ring-1 focus:ring-[#C9962F] w-48 sm:w-56"
              aria-label="Search document filenames and content"
            />
          </div>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-white border border-gray-300 rounded text-xs text-[#131A2E] font-medium"
            aria-label="Filter documents by category"
          >
            <option value="all">All Types</option>
            <option value="interview">Interviews</option>
            <option value="email">Emails</option>
            <option value="report">Reports</option>
            <option value="log">Logs</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* Main split view: Document List & Chunk Explorer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Document List */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
            <span>Case Files ({filteredDocs.length})</span>
            {filteredDocs.length !== documents.length && (
              <span className="text-[10px] text-[#C9962F] lowercase">(filtered from {documents.length})</span>
            )}
          </div>

          {filteredDocs.map((doc) => {
            const isSelected = selectedDoc?.document_id === doc.document_id;
            return (
              <div
                key={doc.document_id}
                onClick={() => setSelectedDoc(doc)}
                className={`case-card p-3 rounded-lg cursor-pointer transition flex items-center justify-between ${
                  isSelected ? 'border-[#C9962F] bg-[#FFFDF9] ring-1 ring-[#C9962F]' : ''
                }`}
                role="button"
                tabIndex={0}
                aria-label={`Select document ${doc.filename}`}
              >
                <div className="flex items-center space-x-2.5 truncate">
                  <FileText className={`w-4 h-4 shrink-0 ${isSelected ? 'text-[#C9962F]' : 'text-gray-400'}`} />
                  <div className="truncate text-left">
                    <div className="text-xs font-bold text-[#131A2E] truncate font-serif">
                      {doc.filename}
                    </div>
                    <div className="text-[10px] text-gray-500 flex items-center space-x-2 mt-0.5">
                      <span className="uppercase font-mono text-[9px] px-1 py-0.2 bg-gray-100 rounded">
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
                    className="p-1 text-gray-400 hover:text-red-600 rounded transition"
                    title="Delete document and revoke citations"
                    aria-label={`Delete ${doc.filename}`}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <ChevronRight className={`w-4 h-4 ${isSelected ? 'text-[#C9962F]' : 'text-gray-300'}`} />
                </div>
              </div>
            );
          })}

          {filteredDocs.length === 0 && (
            <div className="case-card p-6 text-center text-xs text-gray-500 rounded">
              No documents match your search or category filter.
            </div>
          )}
        </div>

        {/* Right: Selected Document Detail & Chunks */}
        <div className="lg:col-span-2">
          {selectedDoc ? (
            <div className="case-card p-5 rounded-lg space-y-4">
              {/* Doc Header */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3">
                <div>
                  <h2 className="text-base font-bold font-serif text-[#131A2E]">
                    {selectedDoc.filename}
                  </h2>
                  <div className="flex items-center space-x-3 text-xs text-gray-500 mt-1">
                    <span className="stamp-label stamp-navy text-[10px]">
                      {selectedDoc.document_type}
                    </span>
                    {selectedDoc.speaker && (
                      <span className="flex items-center text-gray-600">
                        <User className="w-3 h-3 mr-1 text-[#C9962F]" />
                        Speaker: <strong>{selectedDoc.speaker}</strong>
                      </span>
                    )}
                    {selectedDoc.timestamp && (
                      <span className="flex items-center text-gray-600">
                        <Clock className="w-3 h-3 mr-1 text-[#C9962F]" />
                        Time: {selectedDoc.timestamp}
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-right text-[11px] font-mono text-gray-400">
                  ID: {selectedDoc.document_id}
                </div>
              </div>

              {/* Full Text Preview */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-1.5 font-sans">
                  Cleaned Document Content
                </h4>
                <div className="bg-[#FAF8F3] border border-gray-200 rounded p-3 text-xs font-mono max-h-48 overflow-y-auto whitespace-pre-wrap text-gray-800 leading-relaxed">
                  {selectedDoc.cleaned_text || selectedDoc.raw_text}
                </div>
              </div>

              {/* Chunks Explorer */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 font-sans">
                    Traceable Semantic Chunks ({selectedDoc.chunks.length})
                  </h4>
                  <span className="text-[10px] text-gray-400 font-mono">
                    Overlap: 80 chars | Sentence Indexed
                  </span>
                </div>

                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                  {selectedDoc.chunks.map((chunk, idx) => (
                    <div
                      key={chunk.chunk_id}
                      className="bg-white border border-gray-200 rounded p-3 text-xs hover:border-[#C9962F] transition"
                    >
                      <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono mb-1">
                        <span className="font-bold text-[#C9962F]">
                          Chunk #{idx + 1} ({chunk.chunk_id})
                        </span>
                        <span>
                          Sentences: [{chunk.sentence_indices.join(', ')}]
                        </span>
                      </div>
                      <p className="text-gray-800 leading-relaxed font-serif">
                        {chunk.text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="case-card p-12 text-center rounded-lg text-gray-400 text-xs">
              Select a document on the left to inspect content and semantic chunks.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
