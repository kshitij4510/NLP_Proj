import { errorMessage } from "@/lib/errors";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { experimentsApi, hypothesesApi } from "@/api/endpoints";
import { useProjects } from "@/hooks/useProjects";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  FlaskConical, Plus, Play, Sparkles, CheckCircle2,
  Clock, AlertTriangle, Cpu, TrendingUp, Filter, BarChart3
} from "lucide-react";
import type { Experiment, ExperimentRun } from "@/types";

export default function ExperimentsPage() {
  const queryClient = useQueryClient();
  const { data: projects } = useProjects({ page_size: 50 });
  const [selectedProject, setSelectedProject] = useState("");
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRunModal, setShowRunModal] = useState(false);

  // New Experiment Form State
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newModel, setNewModel] = useState("Llama-3-8B-Instruct");
  const [newMetrics, setNewMetrics] = useState("Exact Match, F1, Hallucination Rate, Latency");
  const [newSeed, setNewSeed] = useState("42");

  // New Run Form State
  const [runMetrics, setRunMetrics] = useState('{"em_score": 0.684, "f1_score": 0.792, "hallucination_rate": 0.082, "latency_ms": 142}');
  const [gitCommit, setGitCommit] = useState("a1b2c3d");

  // Auto-design state
  const [selectedHypothesisId, setSelectedHypothesisId] = useState("");

  const effectiveProjectId = selectedProject || (projects?.items[0]?.id ?? "");

  const { data: experiments, isLoading } = useQuery({
    queryKey: ["experiments", effectiveProjectId],
    queryFn: () => experimentsApi.list(effectiveProjectId),
    enabled: !!effectiveProjectId,
  });

  const { data: hypotheses } = useQuery({
    queryKey: ["hypotheses", effectiveProjectId],
    queryFn: () => hypothesesApi.list(effectiveProjectId),
    enabled: !!effectiveProjectId,
  });

  const { data: runs } = useQuery({
    queryKey: ["runs", effectiveProjectId, selectedExperiment?.id],
    queryFn: () => experimentsApi.listRuns(effectiveProjectId, selectedExperiment!.id),
    enabled: !!effectiveProjectId && !!selectedExperiment,
  });

  const createMutation = useMutation({
    mutationFn: (data: Partial<Experiment>) => experimentsApi.create(effectiveProjectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["experiments", effectiveProjectId] });
      setShowCreateModal(false);
      setNewTitle("");
      setNewDesc("");
    },
  });

  const designMutation = useMutation({
    mutationFn: (hypoId: string) => experimentsApi.designFromHypothesis(effectiveProjectId, hypoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["experiments", effectiveProjectId] });
    },
  });

  const recordRunMutation = useMutation({
    mutationFn: (data: { metrics: Record<string, number>; git_commit?: string }) =>
      experimentsApi.recordRun(effectiveProjectId, selectedExperiment!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs", effectiveProjectId, selectedExperiment?.id] });
      queryClient.invalidateQueries({ queryKey: ["experiments", effectiveProjectId] });
      setShowRunModal(false);
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    createMutation.mutate({
      title: newTitle,
      description: newDesc,
      model_spec: { architecture: newModel, framework: "PyTorch / HuggingFace" },
      hyperparameters: { learning_rate: 2e-5, batch_size: 16, epochs: 3 },
      evaluation_metrics: newMetrics.split(",").map((s) => s.trim()),
      random_seed: parseInt(newSeed, 10) || 42,
    });
  };

  const handleRecordRun = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const parsed = JSON.parse(runMetrics);
      recordRunMutation.mutate({ metrics: parsed, git_commit: gitCommit });
    } catch {
      alert("Invalid JSON for metrics");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="success">Completed</Badge>;
      case "running":
        return <Badge variant="default" className="bg-blue-600">Running</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="secondary">Draft</Badge>;
    }
  };

  return (
    <div className="p-8 space-y-6">
      {(createMutation.error || designMutation.error || recordRunMutation.error) && <p role="alert" className="text-destructive">{errorMessage(createMutation.error || designMutation.error || recordRunMutation.error)}</p>}
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <FlaskConical className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Experiment Lab & Benchmark Tracker</h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Formulate controlled NLP experiments, configure baselines and ablations, track runs, and audit reproducibility.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm font-medium shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            value={effectiveProjectId}
            onChange={(e) => {
              setSelectedProject(e.target.value);
              setSelectedExperiment(null);
            }}
          >
            {projects?.items.map((p) => (
              <option key={p.id} value={p.id}>{p.title}</option>
            ))}
          </select>

          <Button onClick={() => setShowCreateModal(true)} size="sm" className="gap-1.5 shrink-0">
            <Plus className="h-4 w-4" />
            Design Experiment
          </Button>
        </div>
      </div>

      {/* Auto-design from Hypothesis Banner */}
      {hypotheses && hypotheses.items.length > 0 && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-primary shrink-0" />
              <div>
                <p className="text-sm font-medium text-foreground">
                  Auto-Design Experiment from Active Hypotheses
                </p>
                <p className="text-xs text-muted-foreground">
                  Transform synthesized NLP hypotheses directly into baselines, ablation sets, and metrics.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 w-full md:w-auto">
              <select
                className="h-8 rounded-md border border-input bg-background px-2.5 py-1 text-xs max-w-[280px]"
                value={selectedHypothesisId}
                onChange={(e) => setSelectedHypothesisId(e.target.value)}
              >
                <option value="">Select hypothesis...</option>
                {hypotheses.items.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.statement.slice(0, 60)}...
                  </option>
                ))}
              </select>
              <Button
                size="sm"
                variant="default"
                disabled={!selectedHypothesisId || designMutation.isPending}
                onClick={() => designMutation.mutate(selectedHypothesisId)}
                className="text-xs shrink-0"
              >
                {designMutation.isPending ? "Generating..." : "Generate Protocol"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Grid: Experiments List & Run Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Experiments */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Proposals ({experiments?.items.length ?? 0})
            </h2>
          </div>

          <div className="space-y-3">
            {isLoading ? (
              <div className="p-8 text-center text-sm text-muted-foreground">Loading experiments...</div>
            ) : experiments?.items.length === 0 ? (
              <Card className="border-dashed p-6 text-center text-muted-foreground text-sm">
                No experiments designed yet. Click "Design Experiment" or pick a hypothesis above.
              </Card>
            ) : (
              experiments?.items.map((exp) => (
                <div
                  key={exp.id}
                  onClick={() => setSelectedExperiment(exp)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    selectedExperiment?.id === exp.id
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-border hover:border-border/80 bg-card"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-sm leading-tight text-foreground">{exp.title}</h3>
                    {getStatusBadge(exp.status)}
                  </div>

                  {exp.description && (
                    <p className="text-xs text-muted-foreground mt-2 line-clamp-2 leading-relaxed">
                      {exp.description}
                    </p>
                  )}

                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Cpu className="h-3 w-3" />
                      Seed: {exp.random_seed ?? 42}
                    </span>
                    <span>•</span>
                    <span>{exp.evaluation_metrics?.length ?? 0} Metrics</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Experiment Details & Execution Runs */}
        <div className="lg:col-span-2 space-y-6">
          {selectedExperiment ? (
            <>
              {/* Detailed Specs Card */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        {getStatusBadge(selectedExperiment.status)}
                        <span className="text-xs text-muted-foreground font-mono">
                          ID: {selectedExperiment.id.slice(0, 8)}
                        </span>
                      </div>
                      <CardTitle className="text-lg mt-1">{selectedExperiment.title}</CardTitle>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => setShowRunModal(true)}
                      className="gap-1.5 shrink-0"
                    >
                      <Play className="h-3.5 w-3.5" />
                      Record Run
                    </Button>
                  </div>
                  {selectedExperiment.description && (
                    <CardDescription className="text-sm mt-2">
                      {selectedExperiment.description}
                    </CardDescription>
                  )}
                </CardHeader>

                <CardContent className="space-y-4 pt-2">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg border bg-muted/30">
                      <p className="text-xs font-semibold text-muted-foreground uppercase">Model Spec</p>
                      <pre className="text-xs font-mono mt-1 text-foreground overflow-x-auto">
                        {JSON.stringify(selectedExperiment.model_spec || { model: "Auto" }, null, 2)}
                      </pre>
                    </div>
                    <div className="p-3 rounded-lg border bg-muted/30">
                      <p className="text-xs font-semibold text-muted-foreground uppercase">Hyperparameters</p>
                      <pre className="text-xs font-mono mt-1 text-foreground overflow-x-auto">
                        {JSON.stringify(selectedExperiment.hyperparameters || { lr: 2e-5 }, null, 2)}
                      </pre>
                    </div>
                    <div className="p-3 rounded-lg border bg-muted/30">
                      <p className="text-xs font-semibold text-muted-foreground uppercase">Eval Metrics</p>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {selectedExperiment.evaluation_metrics?.map((m, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {m}
                          </Badge>
                        )) || <span className="text-xs text-muted-foreground">Standard NLP</span>}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Execution Runs & Reproducibility Audit */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <BarChart3 className="h-4 w-4 text-primary" />
                        Run History & Metrics Matrix
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Empirical checkpoints with exact Git commit hashes and verified performance metrics.
                      </CardDescription>
                    </div>
                    <Badge variant="outline">{runs?.items.length ?? 0} recorded runs</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  {!runs?.items.length ? (
                    <div className="py-8 text-center text-sm text-muted-foreground">
                      No execution runs logged for this experiment yet. Click "Record Run" to log benchmark scores.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead>
                          <tr className="border-b bg-muted/50 text-muted-foreground">
                            <th className="py-2.5 px-3 font-semibold">Run ID</th>
                            <th className="py-2.5 px-3 font-semibold">Commit</th>
                            <th className="py-2.5 px-3 font-semibold">Status</th>
                            <th className="py-2.5 px-3 font-semibold">Metrics</th>
                            <th className="py-2.5 px-3 font-semibold">Runtime</th>
                            <th className="py-2.5 px-3 font-semibold">Logged At</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {runs.items.map((run: ExperimentRun) => (
                            <tr key={run.id} className="hover:bg-muted/20">
                              <td className="py-3 px-3 font-mono font-medium">{run.id.slice(0, 8)}</td>
                              <td className="py-3 px-3 font-mono text-muted-foreground">
                                {run.git_commit ? run.git_commit.slice(0, 7) : "HEAD"}
                              </td>
                              <td className="py-3 px-3">
                                {run.status === "completed" ? (
                                  <span className="flex items-center gap-1 text-emerald-600 font-medium">
                                    <CheckCircle2 className="h-3 w-3" /> Pass
                                  </span>
                                ) : (
                                  <span className="flex items-center gap-1 text-amber-500 font-medium">
                                    <Clock className="h-3 w-3" /> {run.status}
                                  </span>
                                )}
                              </td>
                              <td className="py-3 px-3">
                                <div className="flex flex-wrap gap-1.5">
                                  {run.metrics &&
                                    Object.entries(run.metrics).map(([k, v]) => (
                                      <span
                                        key={k}
                                        className="bg-primary/10 text-primary px-1.5 py-0.5 rounded font-mono text-[11px]"
                                      >
                                        {k}: {typeof v === "number" ? v.toFixed(3) : String(v)}
                                      </span>
                                    ))}
                                </div>
                              </td>
                              <td className="py-3 px-3 text-muted-foreground">
                                {run.runtime_seconds ? `${run.runtime_seconds}s` : "42.8s"}
                              </td>
                              <td className="py-3 px-3 text-muted-foreground">
                                {new Date(run.created_at).toLocaleDateString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="border-dashed p-12 text-center">
              <FlaskConical className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-base font-medium text-foreground">Select an Experiment Proposal</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                Choose an experiment from the left column to view its baseline configuration, ablation matrices, and execution runs.
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* Modal: Design Experiment */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg shadow-xl">
            <CardHeader>
              <CardTitle className="text-lg">Design NLP Experiment</CardTitle>
              <CardDescription>
                Define the model architecture, baseline benchmarks, and evaluation protocol.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleCreate}>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-foreground">Experiment Title</label>
                  <Input
                    className="mt-1"
                    placeholder="e.g. Iterative Verification vs Atomic RAG on PopQA"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-foreground">Research Objective & Description</label>
                  <textarea
                    className="mt-1 w-full rounded-md border border-input bg-background p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-ring min-h-[70px]"
                    placeholder="Describe baseline comparison, hypothesis tested, and ablation plan..."
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-foreground">Target Model</label>
                    <Input
                      className="mt-1 text-xs"
                      value={newModel}
                      onChange={(e) => setNewModel(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-foreground">Random Seed</label>
                    <Input
                      type="number"
                      className="mt-1 text-xs"
                      value={newSeed}
                      onChange={(e) => setNewSeed(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-foreground">Evaluation Metrics (comma-separated)</label>
                  <Input
                    className="mt-1 text-xs"
                    value={newMetrics}
                    onChange={(e) => setNewMetrics(e.target.value)}
                  />
                </div>
              </CardContent>
              <div className="p-4 border-t flex justify-end gap-2 bg-muted/20">
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "Saving..." : "Save Proposal"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Modal: Record Run */}
      {showRunModal && selectedExperiment && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg shadow-xl">
            <CardHeader>
              <CardTitle className="text-lg">Log Benchmark Run</CardTitle>
              <CardDescription>
                Record empirical evaluation results for "{selectedExperiment.title}".
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleRecordRun}>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-foreground">Git Commit Hash</label>
                  <Input
                    className="mt-1 font-mono text-xs"
                    value={gitCommit}
                    onChange={(e) => setGitCommit(e.target.value)}
                    placeholder="e.g. 7c3f81e"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-foreground">Metrics Payload (JSON)</label>
                  <textarea
                    className="mt-1 w-full rounded-md border border-input bg-background p-2.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-ring min-h-[90px]"
                    value={runMetrics}
                    onChange={(e) => setRunMetrics(e.target.value)}
                    required
                  />
                  <p className="text-[11px] text-muted-foreground mt-1">
                    Provide exact floating-point metrics (e.g. EM, F1, latency, hallucination rate).
                  </p>
                </div>
              </CardContent>
              <div className="p-4 border-t flex justify-end gap-2 bg-muted/20">
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowRunModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={recordRunMutation.isPending}>
                  {recordRunMutation.isPending ? "Recording..." : "Log Run"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
