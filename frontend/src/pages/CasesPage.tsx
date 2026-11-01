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
  Shield,
  Check,
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
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="text-xs uppercase font-bold tracking-wider text-blue-600">
            Case Archives & Repository
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
            Investigations Directory
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Manage multi-document incident cases, evaluation benchmarks, and active investigation files.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white text-xs font-semibold transition shadow-sm"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Create Investigation</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 text-xs">
        <button
          onClick={() => setFilter('all')}
          className={`px-3.5 py-1.5 rounded-lg font-semibold transition ${
            filter === 'all'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          All Cases ({cases.length})
        </button>
        <button
          onClick={() => setFilter('demo')}
          className={`px-3.5 py-1.5 rounded-lg font-semibold transition ${
            filter === 'demo'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          Benchmark Cases ({cases.filter((c) => c.is_demo).length})
        </button>
        <button
          onClick={() => setFilter('user')}
          className={`px-3.5 py-1.5 rounded-lg font-semibold transition ${
            filter === 'user'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          User Investigations ({cases.filter((c) => !c.is_demo).length})
        </button>
      </div>

      {/* Cases Grid */}
      {filteredCases.length === 0 ? (
        <div className="case-card p-12 text-center rounded-2xl">
          <FolderArchive className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Cases Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {filter === 'user'
              ? 'You have not created any custom cases yet. Click "Create Investigation" to begin.'
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
                className={`case-card p-5 rounded-2xl flex flex-col justify-between transition-all ${
                  isActive ? 'ring-2 ring-blue-600 border-blue-400 bg-blue-50/15 shadow-md' : 'hover:border-slate-300'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        c.is_demo
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}
                    >
                      {c.is_demo ? 'BENCHMARK' : 'USER CASE'}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  {isEditing ? (
                    <div className="mt-3 space-y-2">
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="w-full text-xs font-semibold p-2 border rounded-lg border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <textarea
                        value={editDesc}
                        onChange={(e) => setEditDesc(e.target.value)}
                        className="w-full text-xs p-2 border rounded-lg border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        rows={2}
                      />
                      <div className="flex space-x-2 pt-1">
                        <button
                          onClick={() => handleUpdateCase(c.case_id)}
                          className="px-3 py-1 bg-blue-600 text-white text-[11px] font-semibold rounded-lg"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingCaseId(null)}
                          className="px-3 py-1 bg-slate-100 text-slate-700 text-[11px] rounded-lg hover:bg-slate-200"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-3">
                      <h3 className="font-bold text-base text-slate-900 leading-snug">
                        {c.name}
                      </h3>
                      <p className="text-xs text-slate-600 mt-1 line-clamp-2 leading-relaxed">
                        {c.description || 'No description provided.'}
                      </p>
                    </div>
                  )}

                  {/* Badges / Metrics */}
                  <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-100 text-center text-xs font-mono">
                    <div className="bg-slate-50 p-2 rounded-xl border border-slate-200/60">
                      <div className="text-slate-400 text-[9px] uppercase font-bold">DOCS</div>
                      <div className="font-bold text-slate-800 text-sm mt-0.5">{c.document_count}</div>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-xl border border-slate-200/60">
                      <div className="text-slate-400 text-[9px] uppercase font-bold">EVENTS</div>
                      <div className="font-bold text-slate-800 text-sm mt-0.5">{c.event_count}</div>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-xl border border-slate-200/60">
                      <div className="text-slate-400 text-[9px] uppercase font-bold">CONFLICTS</div>
                      <div className="font-bold text-rose-600 text-sm mt-0.5">{c.contradiction_count}</div>
                    </div>
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => {
                        setEditingCaseId(c.case_id);
                        setEditName(c.name);
                        setEditDesc(c.description);
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
                      title="Rename Case"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteCase(c.case_id, c.name)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition"
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
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 transition shadow-sm ${
                        isActive
                          ? 'bg-blue-600 text-white hover:bg-blue-500'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      <span>{isActive ? 'Active Dossier' : 'Open Case'}</span>
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
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-base text-slate-900">
                Open New Case File
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition"
              >
                ✕
              </button>
            </div>

            {error && (
              <div className="mt-3 p-2.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center">
                <AlertCircle className="w-4 h-4 mr-1.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleCreateCase} className="mt-4 space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Case Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Investigation into Warehouse Security Breach"
                  value={newCaseName}
                  onChange={(e) => setNewCaseName(e.target.value)}
                  className="w-full p-2.5 border border-slate-300 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Case Synopsis / Description
                </label>
                <textarea
                  rows={3}
                  placeholder="Provide background, date of incident, key locations..."
                  value={newCaseDesc}
                  onChange={(e) => setNewCaseDesc(e.target.value)}
                  className="w-full p-2.5 border border-slate-300 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
                />
              </div>

              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="isDemo"
                  checked={isDemoCase}
                  onChange={(e) => setIsDemoCase(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                />
                <label htmlFor="isDemo" className="text-slate-600 select-none cursor-pointer">
                  Mark as Benchmark / Evaluation Case
                </label>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !newCaseName.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg transition disabled:opacity-50 shadow-sm"
                >
                  {loading ? 'Creating...' : 'Create & Proceed to Ingest'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
