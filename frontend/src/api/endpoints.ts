/**
 * All API endpoint functions.
 * Each function maps 1:1 to a backend route.
 */
import type {
  Claim, Citation, CitationStyle, Experiment, ExperimentRun, GapType,
  Hypothesis, HypothesisStatus, Job, JobStage, Paper, PaperStatus,
  PaginatedResponse, Project, ProjectDetail, ProjectSummary, Report,
  ResearchGap, ResearchPlan, RetrievalResult, TemporalAnalysis, TokenResponse, User,
} from "@/types";
import apiClient from "./client";

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    apiClient.post<User>("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<TokenResponse>("/auth/login", data).then((r) => r.data),

  refresh: (refresh_token: string) =>
    apiClient.post<TokenResponse>("/auth/refresh", { refresh_token }).then((r) => r.data),
};

// ── Projects ──────────────────────────────────────────────────────────────────
export const projectsApi = {
  create: (data: { title: string; description?: string; tags?: string[]; research_question?: { question: string } }) =>
    apiClient.post<Project>("/projects", data).then((r) => r.data),

  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    apiClient.get<PaginatedResponse<Project>>("/projects", { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<ProjectDetail>(`/projects/${id}`).then((r) => r.data),

  update: (id: string, data: Partial<Project>) =>
    apiClient.patch<Project>(`/projects/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/projects/${id}`).then((r) => r.data),

  getSummary: (id: string) =>
    apiClient.get<ProjectSummary>(`/projects/${id}/research/summary`).then((r) => r.data),
};

// ── Papers ────────────────────────────────────────────────────────────────────
export const papersApi = {
  discover: (projectId: string, query: string) => apiClient.post(`/projects/${projectId}/papers/discover/search`, { query }, { timeout: 180_000 }).then(r => r.data),
  add: (projectId: string, data: { doi?: string; arxiv_id?: string; pdf_url?: string; title?: string }) =>
    apiClient.post<Paper>(`/projects/${projectId}/papers`, data).then((r) => r.data),

  list: (projectId: string, params?: { page?: number; page_size?: number; status?: PaperStatus }) =>
    apiClient.get<PaginatedResponse<Paper>>(`/projects/${projectId}/papers`, { params }).then((r) => r.data),

  get: (projectId: string, paperId: string) =>
    apiClient.get<Paper>(`/projects/${projectId}/papers/${paperId}`).then((r) => r.data),

  delete: (projectId: string, paperId: string) =>
    apiClient.delete(`/projects/${projectId}/papers/${paperId}`).then((r) => r.data),

  upload: (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.post<Paper>(`/projects/${projectId}/papers/upload`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
};

// ── Retrieval ──────────────────────────────────────────────────────────────────
export const retrievalApi = {
  search: (data: {
    query: string;
    project_id: string;
    top_k?: number;
    use_reranking?: boolean;
    year_min?: number;
    metadata_filters?: Record<string, string>; year_max?: number;
  }) => apiClient.post<RetrievalResult>("/retrieval/search", data).then((r) => r.data),
};

// ── Research pipeline ─────────────────────────────────────────────────────────
export const researchApi = {
  triggerPipeline: (projectId: string, stage?: JobStage) =>
    apiClient.post(`/projects/${projectId}/research/pipeline/run`, null, {
      params: { stage },
    }).then((r) => r.data),

  triggerSynthesis: (projectId: string) =>
    apiClient.post(`/projects/${projectId}/research/synthesize`).then((r) => r.data),

  getSummary: (projectId: string) =>
    apiClient.get<ProjectSummary>(`/projects/${projectId}/research/summary`).then((r) => r.data),

  getPlan: (projectId: string) =>
    apiClient.get<ResearchPlan>(`/projects/${projectId}/research/plan`).then((r) => r.data),

  generatePlan: (projectId: string) =>
    apiClient.post<ResearchPlan>(`/projects/${projectId}/research/plan/generate`).then((r) => r.data),

  updatePlan: (projectId: string, data: Partial<ResearchPlan>) =>
    apiClient.patch<ResearchPlan>(`/projects/${projectId}/research/plan`, data).then((r) => r.data),

  getTemporal: (projectId: string) =>
    apiClient.get<TemporalAnalysis>(`/projects/${projectId}/research/temporal`).then((r) => r.data),
};

// ── Research gaps ─────────────────────────────────────────────────────────────
export const gapsApi = {
  list: (projectId: string, params?: { gap_type?: GapType; page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<ResearchGap>>(`/projects/${projectId}/research/gaps`, { params }).then((r) => r.data),
};

// ── Hypotheses ────────────────────────────────────────────────────────────────
export const hypothesesApi = {
  create: (projectId: string, data: { statement: string; rationale?: string; gap_id?: string }) =>
    apiClient.post<Hypothesis>(`/projects/${projectId}/research/hypotheses`, data).then((r) => r.data),

  list: (projectId: string, params?: { status?: HypothesisStatus; page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<Hypothesis>>(`/projects/${projectId}/research/hypotheses`, { params }).then((r) => r.data),

  get: (projectId: string, hypothesisId: string) =>
    apiClient.get<Hypothesis>(`/projects/${projectId}/research/hypotheses/${hypothesisId}`).then((r) => r.data),

  generateForGap: (projectId: string, gapId: string) =>
    apiClient.post<Hypothesis[]>(`/projects/${projectId}/research/gaps/${gapId}/hypotheses/generate`).then((r) => r.data),
};

// ── Experiments ───────────────────────────────────────────────────────────────
export const experimentsApi = {
  create: (projectId: string, data: Partial<Experiment>) =>
    apiClient.post<Experiment>(`/projects/${projectId}/experiments`, data).then((r) => r.data),

  designFromHypothesis: (projectId: string, hypothesisId: string) =>
    apiClient.post<Experiment>(`/projects/${projectId}/experiments/design/${hypothesisId}`).then((r) => r.data),

  list: (projectId: string, params?: { page?: number }) =>
    apiClient.get<PaginatedResponse<Experiment>>(`/projects/${projectId}/experiments`, { params }).then((r) => r.data),

  get: (projectId: string, experimentId: string) =>
    apiClient.get<Experiment>(`/projects/${projectId}/experiments/${experimentId}`).then((r) => r.data),

  recordRun: (projectId: string, experimentId: string, data: { metrics: Record<string, number>; git_commit?: string }) =>
    apiClient.post<ExperimentRun>(`/projects/${projectId}/experiments/${experimentId}/runs`, data).then((r) => r.data),

  listRuns: (projectId: string, experimentId: string) =>
    apiClient.get<PaginatedResponse<ExperimentRun>>(`/projects/${projectId}/experiments/${experimentId}/runs`).then((r) => r.data),
};

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportsApi = {
  download: async (projectId: string, reportId: string, format: "ieee" | "markdown" | "bibtex") => {
    const response = await apiClient.get(`/projects/${projectId}/reports/${reportId}/export/${format}`, { responseType: "blob" });
    const url = URL.createObjectURL(response.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = `report_${reportId}.${format === "ieee" ? "tex" : format === "bibtex" ? "bib" : "md"}`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
  generate: (projectId: string, data: { citation_styles?: CitationStyle[]; verify_claims?: boolean }) =>
    apiClient.post<Report>(`/projects/${projectId}/reports/generate`, {
      project_id: projectId,
      ...data,
    }, { timeout: 180_000 }).then((r) => r.data),

  list: (projectId: string) =>
    apiClient.get<PaginatedResponse<Report>>(`/projects/${projectId}/reports`).then((r) => r.data),

  get: (projectId: string, reportId: string) =>
    apiClient.get<Report>(`/projects/${projectId}/reports/${reportId}`).then((r) => r.data),

  exportMarkdownUrl: (projectId: string, reportId: string) =>
    `/api/v1/projects/${projectId}/reports/${reportId}/export/markdown`,

  exportBibtexUrl: (projectId: string, reportId: string) =>
    `/api/v1/projects/${projectId}/reports/${reportId}/export/bibtex`,
};

// ── Jobs ──────────────────────────────────────────────────────────────────────
export const jobsApi = {
  list: (projectId: string, params?: { status?: string; stage?: string; page?: number }) =>
    apiClient.get<PaginatedResponse<Job>>(`/projects/${projectId}/jobs`, { params }).then((r) => r.data),

  get: (projectId: string, jobId: string) =>
    apiClient.get<Job>(`/projects/${projectId}/jobs/${jobId}`).then((r) => r.data),

  getActive: (projectId: string) =>
    apiClient.get<Job | null>(`/projects/${projectId}/jobs/active`).then((r) => r.data),

  cancel: (projectId: string, jobId: string) =>
    apiClient.post(`/projects/${projectId}/jobs/${jobId}/cancel`).then((r) => r.data),
};

// ── Knowledge graph ───────────────────────────────────────────────────────────
export const knowledgeApi = {
  listEntities: (projectId: string, params?: { entity_type?: string; page?: number }) =>
    apiClient.get(`/projects/${projectId}/knowledge/entities`, { params }).then((r) => r.data),

  getEntityDistribution: (projectId: string) =>
    apiClient.get(`/projects/${projectId}/knowledge/entities/distribution`).then((r) => r.data),

  listRelationships: (projectId: string, params?: { relation_type?: string; page?: number }) =>
    apiClient.get(`/projects/${projectId}/knowledge/relationships`, { params }).then((r) => r.data),

  listClaims: (projectId: string, params?: { verification_status?: string; page?: number }) =>
    apiClient.get<{ items: Claim[]; total: number }>(`/projects/${projectId}/knowledge/claims`, { params }).then((r) => r.data),
};
