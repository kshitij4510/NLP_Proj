// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ── Projects ──────────────────────────────────────────────────────────────────
export type ProjectStatus = "created" | "planning" | "active" | "paused" | "completed" | "archived";

export interface ResearchQuestion {
  id: string;
  project_id: string;
  question: string;
  sub_questions?: string[];
  scope?: string;
  keywords?: string[];
  is_primary: boolean;
}

export interface Project {
  id: string;
  owner_id: string;
  title: string;
  description?: string;
  status: ProjectStatus;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  research_questions: ResearchQuestion[];
  paper_count: number;
  hypothesis_count: number;
  experiment_count: number;
}

// ── Papers ────────────────────────────────────────────────────────────────────
export type PaperStatus = "discovered" | "downloading" | "downloaded" | "processing" | "processed" | "failed" | "skipped";

export interface PaperAuthor {
  id: string;
  name: string;
  affiliation?: string;
  orcid?: string;
  position: number;
}

export interface Paper {
  id: string;
  project_id: string;
  doi?: string;
  arxiv_id?: string;
  title: string;
  abstract?: string;
  year?: number;
  venue?: string;
  citation_count: number;
  source: string;
  status: PaperStatus;
  relevance_score?: number;
  authors: PaperAuthor[];
  created_at: string;
  updated_at: string;
}

// ── Retrieval / Evidence ──────────────────────────────────────────────────────
export interface EvidenceSnippet {
  chunk_id: string;
  paper_id: string;
  paper_title: string;
  authors: string[];
  year?: number;
  doi?: string;
  content: string;
  page_number?: number;
  section_title?: string;
  dense_score?: number;
  bm25_score?: number;
  metadata_relevance?: number;
  final_score: number;
}

export interface RetrievalResult {
  query: string;
  evidence: EvidenceSnippet[];
  total_candidates: number;
  retrieval_time_ms: number;
  bm25_candidates: number;
  dense_candidates: number;
  reranked: boolean;
}

// ── Research ──────────────────────────────────────────────────────────────────
export type GapType = "methodological" | "empirical" | "theoretical" | "application" | "replication" | "data";

export interface ResearchGap {
  id: string;
  project_id: string;
  title: string;
  description: string;
  gap_type: GapType;
  importance_score?: number;
  supporting_paper_ids?: string[];
  detected_by: string;
  created_at: string;
  updated_at: string;
}

export type HypothesisStatus = "draft" | "active" | "testing" | "supported" | "refuted" | "inconclusive";

export interface Hypothesis {
  id: string;
  project_id: string;
  gap_id?: string;
  statement: string;
  rationale?: string;
  status: HypothesisStatus;
  confidence?: number;
  testability_score?: number;
  created_at: string;
  updated_at: string;
}

// ── Experiments ───────────────────────────────────────────────────────────────
export type ExperimentStatus = "draft" | "queued" | "running" | "completed" | "failed" | "cancelled";

export interface Experiment {
  id: string;
  project_id: string;
  hypothesis_id?: string;
  dataset_id?: string;
  title: string;
  description?: string;
  status: ExperimentStatus;
  model_spec?: Record<string, unknown>;
  hyperparameters?: Record<string, unknown>;
  random_seed?: number;
  evaluation_metrics?: string[];
  created_at: string;
  updated_at: string;
}

export interface ExperimentRun {
  id: string;
  experiment_id: string;
  status: ExperimentStatus;
  git_commit?: string;
  metrics?: Record<string, number>;
  runtime_seconds?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

// ── Knowledge Graph ───────────────────────────────────────────────────────────
export type EntityType = "MODEL" | "DATASET" | "TASK" | "METRIC" | "METHOD" | "BENCHMARK" | "ORGANIZATION";
export type VerificationStatus = "SUPPORTED" | "PARTIALLY_SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT_EVIDENCE" | "PENDING";

export interface KnowledgeEntity {
  id: string;
  name: string;
  entity_type: EntityType;
  confidence: number;
  paper_id: string;
}

export interface KnowledgeRelationship {
  id: string;
  source: string;
  target: string;
  relation_type: string;
  confidence: number;
  evidence_snippet?: string;
}

export interface ClaimEvidenceLink {
  id: string;
  chunk_id: string;
  relevance_score: number;
  evidence_snippet?: string;
  section_title?: string;
  page_number?: number;
}

export interface Claim {
  id: string;
  claim_text: string;
  verification_status: VerificationStatus;
  artifact_type: string;
  confidence?: number;
  evidence_links?: ClaimEvidenceLink[];
}

// ── Reports ───────────────────────────────────────────────────────────────────
export type ReportStatus = "draft" | "generating" | "verifying" | "completed" | "failed";
export type CitationStyle = "apa" | "ieee" | "bibtex";

export interface Citation {
  id: string;
  paper_id: string;
  style: CitationStyle;
  formatted_citation: string;
  in_text_citation?: string;
}

export interface Report {
  id: string;
  project_id: string;
  title: string;
  status: ReportStatus;
  abstract?: string;
  research_question_section?: string;
  background?: string;
  literature_review?: string;
  research_landscape?: string;
  method_comparison?: string;
  research_gaps_section?: string;
  hypotheses_section?: string;
  experimental_design?: string;
  results?: string;
  ablation_study?: string;
  limitations?: string;
  future_work?: string;
  conclusion?: string;
  unsupported_claim_count: number;
  citations: Citation[];
  created_at: string;
  updated_at: string;
}

// ── Jobs ──────────────────────────────────────────────────────────────────────
export type JobStage =
  | "PLANNING" | "DISCOVERY" | "INGESTION" | "ANALYSIS" | "EXTRACTION"
  | "SYNTHESIS" | "GAP_ANALYSIS" | "HYPOTHESIS" | "EXPERIMENT_DESIGN"
  | "VERIFICATION" | "REPORTING" | "COMPLETED";

export type JobStatus = "pending" | "running" | "completed" | "failed" | "cancelled" | "retrying";

export interface Job {
  id: string;
  project_id: string;
  stage: JobStage;
  status: JobStatus;
  progress: number;
  started_at?: string;
  completed_at?: string;
  retry_count: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

// ── Pagination ────────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ── Project summary ───────────────────────────────────────────────────────────
export interface ProjectSummary {
  papers: number;
  research_gaps: number;
  hypotheses: number;
  experiments: number;
  reports: number;
  claims: number;
}

// ── Research Plan & Temporal Analysis ─────────────────────────────────────────
export interface ResearchPlan {
  research_question: string;
  problem_definition: string;
  sub_questions: string[];
  keywords: string[];
  related_concepts: string[];
  search_strategy: string[];
  inclusion_criteria: string[];
  exclusion_criteria: string[];
  candidate_datasets: string[];
  metrics: string[];
  potential_experiments: string[];
  is_approved: boolean;
}

export interface TemporalPoint {
  year: number;
  paper_count: number;
  top_models: string[];
  top_datasets: string[];
  top_topics: string[];
}

export interface TemporalAnalysis {
  project_id: string;
  timeline: TemporalPoint[];
  model_evolution: { name: string; counts: Record<number, number> }[];
  dataset_popularity: { name: string; counts: Record<number, number> }[];
  topic_trends: { year: number; papers: number; topics: string[] }[];
}
