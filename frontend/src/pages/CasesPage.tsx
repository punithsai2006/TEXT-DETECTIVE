import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCase } from '../context/CaseContext';
import { api } from '../services/api';
import {
  FolderArchive,
  PlusCircle,
  Trash2,
  Edit2,
  Play,
  ArrowRight,
  AlertCircle,
  FileText,
  Clock,
  Sparkles,
} from 'lucide-react';

export const CasesPage: React.FC = () => {
  const { cases, activeCaseId, setActiveCaseId, refreshCases } = useCase();
  const navigate = useNavigate();

  const [filter, setFilter] = useState<'all' | 'user' | 'demo'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCaseName, setNewCaseName] = useState('');
  const [newCaseDesc, setNewCaseDesc] = useState('');
  const [isDemoCase, setIsDemoCase] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Edit State
  const [editingCaseId, setEditingCaseId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  const filteredCases = cases.filter((c) => {
    if (filter === 'user') return !c.is_demo;
    if (filter === 'demo') return c.is_demo;
    return true;
  });

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCaseName.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const created = await api.createCase(newCaseName.trim(), newCaseDesc.trim(), isDemoCase);
      await refreshCases();
      setActiveCaseId(created.case_id);
      setShowCreateModal(false);
      setNewCaseName('');
      setNewCaseDesc('');
      navigate('/new');
    } catch (err: any) {
      setError(err.message || 'Failed to create case');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCase = async (caseId: string, caseName: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete case '${caseName}'? All documents, vectors, and reports will be deleted.`)) {
      return;
    }
    try {
      await api.deleteCase(caseId);
      await refreshCases();
      if (activeCaseId === caseId) {
        setActiveCaseId(null);
      }
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleUpdateCase = async (caseId: string) => {
    if (!editName.trim()) return;
    try {
      await api.updateCase(caseId, { name: editName.trim(), description: editDesc.trim() });
      await refreshCases();
      setEditingCaseId(null);
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-gray-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-widest text-[#C9962F] font-serif">
            Case Archives & Repositories
          </div>
          <h1 className="text-xl font-bold font-serif text-[#131A2E] mt-0.5">
            Investigations Directory
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Manage multi-document investigation records and benchmark evaluation cases.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center space-x-1.5 px-3.5 py-2 rounded bg-[#C9962F] text-[#131A2E] text-xs font-bold hover:bg-[#E0B354] transition shadow"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Create Case File</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 text-xs">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1.5 rounded-md font-medium transition ${
            filter === 'all'
              ? 'bg-[#131A2E] text-white font-bold'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          All Cases ({cases.length})
        </button>
        <button
          onClick={() => setFilter('demo')}
          className={`px-3 py-1.5 rounded-md font-medium transition ${
            filter === 'demo'
              ? 'bg-[#131A2E] text-white font-bold'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          Demo Benchmarks ({cases.filter((c) => c.is_demo).length})
        </button>
        <button
          onClick={() => setFilter('user')}
          className={`px-3 py-1.5 rounded-md font-medium transition ${
            filter === 'user'
              ? 'bg-[#131A2E] text-white font-bold'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          User Investigations ({cases.filter((c) => !c.is_demo).length})
        </button>
      </div>

      {/* Cases Grid */}
      {filteredCases.length === 0 ? (
        <div className="case-card p-12 text-center rounded-lg">
          <FolderArchive className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-gray-700">No Cases Found</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            {filter === 'user'
              ? 'You have not created any custom cases yet. Click "Create Case File" to begin.'
              : 'No matching cases in this category.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCases.map((c) => {
            const isActive = c.case_id === activeCaseId;
            const isEditing = editingCaseId === c.case_id;

            return (
              <div
                key={c.case_id}
                className={`case-card p-4 rounded-lg flex flex-col justify-between transition ${
                  isActive ? 'ring-2 ring-[#C9962F] border-[#C9962F]' : ''
                }`}
              >
                <div>
                  <div className="flex items-center justify-between pb-2 border-b border-gray-100">
                    <span
                      className={`stamp-label text-[9px] ${
                        c.is_demo ? 'stamp-gold' : 'stamp-navy'
                      }`}
                    >
                      {c.is_demo ? 'FICTIONAL BENCHMARK' : 'USER CASE'}
                    </span>
                    <span className="text-[10px] text-gray-400 font-mono">
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  {isEditing ? (
                    <div className="mt-2 space-y-2">
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="w-full text-xs font-bold p-1.5 border rounded border-gray-300"
                      />
                      <textarea
                        value={editDesc}
                        onChange={(e) => setEditDesc(e.target.value)}
                        className="w-full text-xs p-1.5 border rounded border-gray-300"
                        rows={2}
                      />
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleUpdateCase(c.case_id)}
                          className="px-2 py-1 bg-[#131A2E] text-white text-[11px] rounded"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingCaseId(null)}
                          className="px-2 py-1 bg-gray-200 text-gray-700 text-[11px] rounded"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-2">
                      <h3 className="font-serif font-bold text-base text-[#131A2E] leading-snug">
                        {c.name}
                      </h3>
                      <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                        {c.description || 'No description provided.'}
                      </p>
                    </div>
                  )}

                  {/* Badges / Metrics */}
                  <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-gray-100 text-center text-xs font-mono">
                    <div className="bg-[#FAF8F3] p-1.5 rounded">
                      <div className="text-gray-400 text-[10px]">DOCS</div>
                      <div className="font-bold text-gray-700">{c.document_count}</div>
                    </div>
                    <div className="bg-[#FAF8F3] p-1.5 rounded">
                      <div className="text-gray-400 text-[10px]">EVENTS</div>
                      <div className="font-bold text-gray-700">{c.event_count}</div>
                    </div>
                    <div className="bg-[#FAF8F3] p-1.5 rounded">
                      <div className="text-gray-400 text-[10px]">CONFLICTS</div>
                      <div className="font-bold text-red-600">{c.contradiction_count}</div>
                    </div>
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => {
                        setEditingCaseId(c.case_id);
                        setEditName(c.name);
                        setEditDesc(c.description);
                      }}
                      className="p-1.5 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100"
                      title="Rename Case"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteCase(c.case_id, c.name)}
                      className="p-1.5 rounded text-gray-400 hover:text-red-600 hover:bg-red-50"
                      title="Delete Case"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <button
                      onClick={() => {
                        setActiveCaseId(c.case_id);
                        navigate('/timeline');
                      }}
                      className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center space-x-1 transition ${
                        isActive
                          ? 'bg-[#131A2E] text-white hover:bg-[#1D2744]'
                          : 'bg-[#FAF8F3] text-gray-700 hover:bg-[#F4F0E6] border border-gray-200'
                      }`}
                    >
                      <span>{isActive ? 'Explore Dossier' : 'Open Case'}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-2xl border border-[#C9962F]">
            <div className="flex items-center justify-between pb-3 border-b border-gray-200">
              <h3 className="font-serif font-bold text-base text-[#131A2E]">
                Open New Case File
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {error && (
              <div className="mt-3 p-2.5 bg-red-50 border border-red-200 text-red-700 rounded text-xs flex items-center">
                <AlertCircle className="w-4 h-4 mr-1.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleCreateCase} className="mt-4 space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-gray-700 mb-1">
                  Case Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Investigation into Warehouse Security Breach"
                  value={newCaseName}
                  onChange={(e) => setNewCaseName(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded focus:border-[#C9962F] focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">
                  Case Synopsis / Description
                </label>
                <textarea
                  rows={3}
                  placeholder="Provide background, date of incident, key locations..."
                  value={newCaseDesc}
                  onChange={(e) => setNewCaseDesc(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded focus:border-[#C9962F] focus:outline-none"
                />
              </div>

              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="isDemo"
                  checked={isDemoCase}
                  onChange={(e) => setIsDemoCase(e.target.checked)}
                  className="rounded text-[#C9962F] focus:ring-[#C9962F]"
                />
                <label htmlFor="isDemo" className="text-gray-600 select-none">
                  Mark as Demo / Synthetic Benchmark Case
                </label>
              </div>

              <div className="pt-3 border-t border-gray-100 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !newCaseName.trim()}
                  className="px-4 py-1.5 bg-[#C9962F] text-[#131A2E] font-bold rounded hover:bg-[#E0B354] transition disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create & Proceed to Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
