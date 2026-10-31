export type DocumentType = 'interview' | 'email' | 'report' | 'log' | 'other';
export type EntityType = 'person' | 'organization' | 'location' | 'object';
export type CaseStatus =
  | 'created'
  | 'ingesting'
  | 'extracting'
  | 'retrieving'
  | 'checking_contradictions'
  | 'scoring_hypotheses'
  | 'generating_report'
  | 'completed'
  | 'outdated'
  | 'failed';

export interface TextChunk {
  chunk_id: string;
  case_id: string;
  document_id: string;
  filename: string;
  document_type: DocumentType;
  speaker?: string;
  timestamp?: string;
  page_number?: number;
  text: string;
  sentence_indices: number[];
  char_start: number;
  char_end: number;
}

export interface DocumentMetadata {
  document_id: string;
  case_id: string;
  filename: string;
  document_type: DocumentType;
  speaker?: string;
  author?: string;
  timestamp?: string;
  description?: string;
  file_size_bytes: number;
  raw_text: string;
  cleaned_text: string;
  chunks: TextChunk[];
  uploaded_at: string;
  status: string;
  warning?: string;
}

export interface Entity {
  entity_id: string;
  name: string;
  entity_type: EntityType;
  mentions_count: number;
  document_ids: string[];
  source_sentences: string[];
  metadata?: Record<string, any>;
}

export interface Event {
  event_id: string;
  description: string;
  participants: string[];
  location?: string;
  time_str?: string;
  parsed_timestamp?: string;
  uses_objects: string[];
  document_id: string;
  document_name: string;
  source_sentence: string;
  uncertainty: boolean;
}

export interface TimelineEntry {
  entry_id: string;
  event_id: string;
  timestamp_display: string;
  event_description: string;
  participants: string[];
  location?: string;
  document_name: string;
  document_type: DocumentType;
  source_sentence: string;
  is_uncertain: boolean;
  sort_key: string;
}

export interface CaseGraphNode {
  id: string;
  label: string;
  node_type: string;
  sub_type?: string;
  properties?: Record<string, any>;
}

export interface CaseGraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  evidence_sentence?: string;
}

export interface CaseGraph {
  nodes: CaseGraphNode[];
  edges: CaseGraphEdge[];
}

export interface EvidenceItem {
  evidence_id: string;
  case_id: string;
  document_id: string;
  document_name: string;
  document_type: DocumentType;
  chunk_id: string;
  text: string;
  speaker?: string;
  timestamp?: string;
  sentence_indices: number[];
  score: number;
  retrieval_method: string;
}

export interface ContradictionItem {
  id: string;
  case_id: string;
  statement_a: string;
  statement_b: string;
  doc_a_id: string;
  doc_b_id: string;
  doc_a_name: string;
  doc_b_name: string;
  speaker_a?: string;
  speaker_b?: string;
  timestamp_a?: string;
  timestamp_b?: string;
  entity_event_link: string;
  contradiction_type: 'confirmed_contradiction' | 'possible_contradiction' | 'agreement' | 'neutral';
  nli_label: 'contradiction' | 'entailment' | 'neutral';
  confidence: number;
  explanation: string;
  resolution_status: 'unresolved' | 'resolved' | 'investigating';
  source_sentences: string[];
}

export interface HypothesisClaim {
  claim_id: string;
  text: string;
  supporting_evidence_ids: string[];
  conflicting_evidence_ids: string[];
  contributing_documents: string[];
  contributing_speakers: string[];
  is_corroborated: boolean;
  unresolved_conflicts_count: number;
}

export interface Hypothesis {
  hypothesis_id: string;
  case_id: string;
  title: string;
  description: string;
  origin: 'user' | 'generated';
  claims: HypothesisClaim[];
  support_score: number;
  conflict_score: number;
  corroboration_score: number;
  conflict_penalty: number;
  total_score: number;
  rank: number;
  is_proposed_explanation: boolean;
  explanation: string;
  uncertainty_warning?: string;
}

export interface ControllerFeedbackLoopEvent {
  loop_name: string;
  iteration: number;
  trigger_reason: string;
  action_taken: string;
  result_summary: string;
  timestamp: string;
}

export interface AnalysisStatus {
  case_id: string;
  status: CaseStatus;
  current_module: string;
  progress_percentage: number;
  message: string;
  feedback_loops: ControllerFeedbackLoopEvent[];
  updated_at: string;
  error?: string;
}

export interface InvestigationReport {
  report_id: string;
  case_id: string;
  case_name: string;
  generated_at: string;
  case_overview: string;
  documents_analyzed: Array<{
    document_id: string;
    filename: string;
    document_type: string;
    speaker?: string;
    timestamp?: string;
    chunk_count: number;
    file_size_bytes: number;
  }>;
  investigation_summary: string;
  extracted_entities: Entity[];
  important_events: Event[];
  chronological_timeline: TimelineEntry[];
  key_evidence: EvidenceItem[];
  agreements: ContradictionItem[];
  contradictions: ContradictionItem[];
  candidate_hypotheses: Hypothesis[];
  score_breakdown: Array<{
    rank: number;
    hypothesis_id: string;
    title: string;
    origin: string;
    support: number;
    conflict: number;
    corroboration: number;
    conflict_penalty: number;
    total_score: number;
    is_proposed_explanation: boolean;
  }>;
  proposed_explanation?: Hypothesis;
  supporting_evidence: EvidenceItem[];
  conflicting_evidence: EvidenceItem[];
  unresolved_questions: string[];
  limitations_and_uncertainty: string;
  source_references: Array<{
    ref_id: string;
    document: string;
    document_type: string;
    speaker: string;
    timestamp: string;
    sentence_indices: number[];
    excerpt: string;
  }>;
}

export interface Case {
  case_id: string;
  name: string;
  description: string;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  status: CaseStatus;
  document_count: number;
  entity_count: number;
  event_count: number;
  contradiction_count: number;
  hypothesis_count: number;
  single_document_warning: boolean;
}

export interface AskQuestionResponse {
  question: string;
  answer: string;
  evidence: EvidenceItem[];
  sources: Array<{
    source_num: number;
    document: string;
    speaker?: string;
    timestamp?: string;
    chunk_id: string;
  }>;
  model_used: string;
  is_mock: boolean;
  uncertainty_note?: string;
}
