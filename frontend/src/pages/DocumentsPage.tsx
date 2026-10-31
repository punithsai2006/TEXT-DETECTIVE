import React, { useEffect, useState } from 'react';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import { DocumentMetadata, TextChunk } from '../types';
import {
  FileText,
  User,
  Clock,
  Trash2,
  ChevronRight,
  AlertTriangle,
  FolderOpen,
} from 'lucide-react';

export const DocumentsPage: React.FC = () => {
  const { activeCaseId, activeCase, refreshCases } = useCase();
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
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
    if (!window.confirm(`Delete document '${filename}'?`)) return;
    try {
      await api.deleteDocument(docId);
      await refreshCases();
      setDocuments((prev) => prev.filter((d) => d.document_id !== docId));
      if (selectedDoc?.document_id === docId) {
        setSelectedDoc(null);
      }
    } catch (e: any) {
      alert(`Delete failed: ${e.message}`);
    }
  };

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
      <div className="flex items-center justify-between border-b border-gray-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
            Evidence Ingestion Files
          </div>
          <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
            Documents Explorer
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Inspected {documents.length} source documents for case <strong>{activeCase?.name}</strong>.
          </p>
        </div>
      </div>

      {/* Main split view: Document List & Chunk Explorer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Document List */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
            Ingested Case Files ({documents.length})
          </h3>

          {documents.map((doc) => {
            const isSelected = selectedDoc?.document_id === doc.document_id;
            return (
              <div
                key={doc.document_id}
                onClick={() => setSelectedDoc(doc)}
                className={`case-card p-3 rounded-lg cursor-pointer transition flex items-center justify-between ${
                  isSelected ? 'border-[#C9962F] bg-[#FFFDF9] ring-1 ring-[#C9962F]' : ''
                }`}
              >
                <div className="flex items-center space-x-2.5 truncate">
                  <FileText className={`w-4 h-4 shrink-0 ${isSelected ? 'text-[#C9962F]' : 'text-gray-400'}`} />
                  <div className="truncate text-left">
                    <div className="text-xs font-bold text-[#131A2E] truncate font-serif">
                      {doc.filename}
                    </div>
                    <div className="text-[10px] text-gray-500 flex items-center space-x-2 mt-0.5 font-mono">
                      <span className="uppercase text-[#A87A1E] font-semibold">{doc.document_type}</span>
                      <span>•</span>
                      <span>{doc.chunks.length} chunks</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(doc.document_id, doc.filename);
                    }}
                    className="p-1 text-gray-300 hover:text-red-600 rounded transition"
                    title="Delete document"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <ChevronRight className="w-4 h-4 text-gray-300" />
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Selected Document Detail & Chunks */}
        <div className="lg:col-span-2 space-y-4">
          {selectedDoc ? (
            <div className="case-card p-5 rounded-lg space-y-4">
              {/* Document Meta Header */}
              <div className="border-b border-gray-100 pb-3 flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="stamp-label stamp-navy text-[10px]">
                      {selectedDoc.document_type}
                    </span>
                    <span className="text-[10px] text-gray-400 font-mono">
                      ID: {selectedDoc.document_id}
                    </span>
                  </div>
                  <h2 className="text-base font-bold font-serif text-[#131A2E] mt-1">
                    {selectedDoc.filename}
                  </h2>
                </div>

                <div className="text-right text-xs text-gray-500">
                  {selectedDoc.speaker && (
                    <div className="flex items-center justify-end text-[#C9962F] font-semibold">
                      <User className="w-3 h-3 mr-1" />
                      <span>{selectedDoc.speaker}</span>
                    </div>
                  )}
                  {selectedDoc.timestamp && (
                    <div className="flex items-center justify-end text-gray-400 text-[11px] mt-0.5">
                      <Clock className="w-3 h-3 mr-1" />
                      <span>{selectedDoc.timestamp}</span>
                    </div>
                  )}
                </div>
              </div>

              {selectedDoc.warning && (
                <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded flex items-center">
                  <AlertTriangle className="w-4 h-4 mr-2 shrink-0 text-amber-600" />
                  <span>{selectedDoc.warning}</span>
                </div>
              )}

              {/* Chunks Explorer */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-gray-700 mb-2 font-mono">
                  Semantic Chunks ({selectedDoc.chunks.length})
                </h4>
                <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
                  {selectedDoc.chunks.map((chk, i) => (
                    <div
                      key={chk.chunk_id || i}
                      className="p-3 bg-[#FAF8F3] border border-gray-200 rounded text-xs leading-relaxed"
                    >
                      <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono mb-1.5 pb-1 border-b border-gray-200">
                        <span>Chunk #{i + 1} ({chk.chunk_id})</span>
                        <span>Sentences: {chk.sentence_indices.map((idx) => `#${idx + 1}`).join(', ')}</span>
                      </div>
                      <p className="text-gray-800 font-serif italic">"{chk.text}"</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="case-card p-12 text-center rounded-lg text-gray-400 text-xs">
              Select a document from the left list to inspect chunks and sentence attributions.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
