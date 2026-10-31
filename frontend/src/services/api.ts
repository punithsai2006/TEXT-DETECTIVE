import {
  AnalysisRunRecord,
  AnalysisStatus,
  AskQuestionResponse,
  Case,
  CaseGraph,
  ContradictionItem,
  DocumentMetadata,
  Entity,
  Event,
  EvidenceItem,
  Hypothesis,
  InvestigationReport,
  ProvenanceValidationReport,
  ReviewStatus,
  TimelineEntry,
} from '../types';

const API_BASE = '/api';

export const api = {
  // Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to fetch system health');
    return res.json();
  },

  // Cases
  async listCases(): Promise<Case[]> {
    const res = await fetch(`${API_BASE}/cases`);
    if (!res.ok) throw new Error('Failed to list cases');
    return res.json();
  },

  async getCase(caseId: string): Promise<Case> {
    const res = await fetch(`${API_BASE}/cases/${caseId}`);
    if (!res.ok) throw new Error(`Failed to get case ${caseId}`);
    return res.json();
  },

  async createCase(name: string, description: string = '', isDemo: boolean = false): Promise<Case> {
    const res = await fetch(`${API_BASE}/cases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description, is_demo: isDemo }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create case' }));
      throw new Error(err.detail || 'Failed to create case');
    }
    return res.json();
  },

  async updateCase(caseId: string, data: { name?: string; description?: string }): Promise<Case> {
    const res = await fetch(`${API_BASE}/cases/${caseId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Failed to update case ${caseId}`);
    return res.json();
  },

  async deleteCase(caseId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/cases/${caseId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Failed to delete case ${caseId}`);
  },

  // Documents
  async getCaseDocuments(caseId: string): Promise<DocumentMetadata[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/documents`);
    if (!res.ok) throw new Error(`Failed to get documents for case ${caseId}`);
    return res.json();
  },

  async uploadDocuments(caseId: string, formData: FormData): Promise<DocumentMetadata[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/documents`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to upload documents' }));
      throw new Error(err.detail || 'Failed to upload documents');
    }
    return res.json();
  },

  async deleteDocument(documentId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/documents/${documentId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Failed to delete document ${documentId}`);
  },

  // Analysis & Orchestration
  async runAnalysis(
    caseId: string,
    hypotheses?: Array<{ title: string; description: string }>
  ): Promise<InvestigationReport> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(hypotheses || null),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(err.detail || 'Analysis failed');
    }
    return res.json();
  },

  async getAnalysisStatus(caseId: string): Promise<AnalysisStatus> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/analysis-status`);
    if (!res.ok) throw new Error(`Failed to get status for case ${caseId}`);
    return res.json();
  },

  async getAnalysisResults(caseId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/analysis-results`);
    if (!res.ok) throw new Error(`Failed to get analysis results for case ${caseId}`);
    return res.json();
  },

  // Extraction & Graph
  async getTimeline(caseId: string): Promise<TimelineEntry[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/timeline`);
    if (!res.ok) throw new Error('Failed to get timeline');
    return res.json();
  },

  async getEntities(caseId: string): Promise<Entity[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/entities`);
    if (!res.ok) throw new Error('Failed to get entities');
    return res.json();
  },

  async getEvents(caseId: string): Promise<Event[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/events`);
    if (!res.ok) throw new Error('Failed to get events');
    return res.json();
  },

  async getCaseGraph(caseId: string): Promise<CaseGraph> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/case-graph`);
    if (!res.ok) throw new Error('Failed to get case graph');
    return res.json();
  },

  // Evidence Retrieval
  async searchEvidence(caseId: string, query: string, topK: number = 10, threshold: number = 0.0): Promise<EvidenceItem[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/evidence/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK, threshold }),
    });
    if (!res.ok) throw new Error('Failed to search evidence');
    return res.json();
  },

  async getKeyEvidence(caseId: string): Promise<EvidenceItem[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/evidence`);
    if (!res.ok) throw new Error('Failed to get key evidence');
    return res.json();
  },

  // Contradictions
  async getContradictions(caseId: string): Promise<ContradictionItem[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/contradictions`);
    if (!res.ok) throw new Error('Failed to get contradictions');
    return res.json();
  },

  // Hypotheses
  async getHypotheses(caseId: string): Promise<Hypothesis[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/hypotheses`);
    if (!res.ok) throw new Error('Failed to get hypotheses');
    return res.json();
  },

  async addHypotheses(caseId: string, hypotheses: Array<{ title: string; description: string }>): Promise<Hypothesis[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/hypotheses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(hypotheses),
    });
    if (!res.ok) throw new Error('Failed to add hypotheses');
    return res.json();
  },

  async rescoreHypotheses(caseId: string): Promise<Hypothesis[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/hypotheses/score`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to rescore hypotheses');
    return res.json();
  },

  // Natural Language Q&A
  async askQuestion(caseId: string, question: string, topK: number = 5): Promise<AskQuestionResponse> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: topK }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Question answering failed' }));
      throw new Error(err.detail || 'Question answering failed');
    }
    return res.json();
  },

  // Report
  async getReport(caseId: string): Promise<InvestigationReport> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/report`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Report not ready' }));
      throw new Error(err.detail || 'Report not ready');
    }
    return res.json();
  },

  getReportDownloadUrl(caseId: string, format: 'markdown' | 'json' | 'html'): string {
    return `${API_BASE}/cases/${caseId}/report/download?format=${format}`;
  },

  // Contradiction Review (Task 5)
  async reviewContradiction(
    caseId: string,
    contradictionId: string,
    reviewStatus: ReviewStatus,
    reviewerId: string = 'analyst_1',
    reviewNotes?: string
  ): Promise<ContradictionItem> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/contradictions/${contradictionId}/review`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ review_status: reviewStatus, reviewer_id: reviewerId, review_notes: reviewNotes }),
    });
    if (!res.ok) throw new Error('Failed to update contradiction review');
    return res.json();
  },

  // Provenance Validation (Task 2)
  async getProvenanceReport(caseId: string): Promise<ProvenanceValidationReport> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/provenance`);
    if (!res.ok) throw new Error('Failed to fetch provenance report');
    return res.json();
  },

  // Reproducible Analysis Runs (Task 6)
  async listAnalysisRuns(caseId: string): Promise<AnalysisRunRecord[]> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/runs`);
    if (!res.ok) throw new Error('Failed to list analysis runs');
    return res.json();
  },

  async deleteCaseDocument(caseId: string, documentId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/documents/${documentId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Failed to delete document ${documentId}`);
  },
};
