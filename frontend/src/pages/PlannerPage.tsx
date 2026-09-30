import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useProjects } from "@/hooks/useProjects";
import { researchApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Compass, CheckCircle2, RefreshCw, Play, Sparkles, Layers,
  ListFilter, Database, Gauge, FlaskConical, AlertCircle
} from "lucide-react";
import type { ResearchPlan } from "@/types";

export default function PlannerPage() {
  const queryClient = useQueryClient();
  const { data: projects } = useProjects({ page_size: 50 });
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [editedPlan, setEditedPlan] = useState<ResearchPlan | null>(null);

  // Default to first project
  useEffect(() => {
    if (projects?.items && projects.items.length > 0 && !selectedProjectId) {
      setSelectedProjectId(projects.items[0].id);
    }
  }, [projects, selectedProjectId]);

  const { data: plan, isLoading, refetch } = useQuery({
    queryKey: ["research-plan", selectedProjectId],
    queryFn: () => researchApi.getPlan(selectedProjectId),
    enabled: !!selectedProjectId,
  });

  useEffect(() => {
    if (plan) {
      setEditedPlan(plan);
    }
  }, [plan]);

  const generateMutation = useMutation({
    mutationFn: () => researchApi.generatePlan(selectedProjectId),
    onSuccess: (newPlan) => {
      setEditedPlan(newPlan);
      queryClient.invalidateQueries({ queryKey: ["research-plan", selectedProjectId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (updated: Partial<ResearchPlan>) =>
      researchApi.updatePlan(selectedProjectId, updated),
    onSuccess: (saved) => {
      setEditedPlan(saved);
      queryClient.invalidateQueries({ queryKey: ["research-plan", selectedProjectId] });
    },
  });

  const runPipelineMutation = useMutation({
    mutationFn: () => researchApi.triggerPipeline(selectedProjectId, "DISCOVERY"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["active-job", selectedProjectId] });
    },
  });

  const handleApproveAndProceed = () => {
    if (!editedPlan) return;
    updateMutation.mutate({ ...editedPlan, is_approved: true }, {
      onSuccess: () => {
        runPipelineMutation.mutate();
      }
    });
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b pb-6">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1 uppercase tracking-wider">
            <Compass className="h-4 w-4" /> Autonomous Research Planner (Module B)
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Research Plan Formulation</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Formalizes search strategies, criteria, datasets, and hypotheses before autonomous execution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            className="h-10 rounded-lg border border-input bg-card px-3 py-2 text-sm shadow-sm"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
          >
            {projects?.items.map((p) => (
              <option key={p.id} value={p.id}>{p.title}</option>
            ))}
          </select>

          <Button
            variant="outline"
            size="sm"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending || !selectedProjectId}
          >
            <RefreshCw className={`h-4 w-4 mr-1.5 ${generateMutation.isPending ? "animate-spin" : ""}`} />
            Regenerate
          </Button>

          <Button
            size="sm"
            className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
            onClick={handleApproveAndProceed}
            disabled={updateMutation.isPending || runPipelineMutation.isPending || !editedPlan}
          >
            <CheckCircle2 className="h-4 w-4 mr-1.5" />
            {editedPlan?.is_approved ? "Approved · Run Pipeline" : "Approve Plan & Discover"}
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : editedPlan ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Plan Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Approval Status Banner */}
            <div className={`p-4 rounded-xl border flex items-center justify-between ${
              editedPlan.is_approved
                ? "bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/30 dark:border-emerald-800 dark:text-emerald-200"
                : "bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950/30 dark:border-amber-800 dark:text-amber-200"
            }`}>
              <div className="flex items-center gap-3">
                {editedPlan.is_approved ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <AlertCircle className="h-5 w-5 text-amber-600" />}
                <div>
                  <p className="font-semibold text-sm">
                    {editedPlan.is_approved ? "Research Plan Approved" : "Awaiting Researcher Review & Approval"}
                  </p>
                  <p className="text-xs opacity-90">
                    {editedPlan.is_approved
                      ? "Search criteria and scope locked. Discovery can proceed autonomously."
                      : "Review generated search strategy and criteria below. Click 'Approve Plan & Discover' when ready."}
                  </p>
                </div>
              </div>
              <Badge variant={editedPlan.is_approved ? "outline" : "secondary"}>
                {editedPlan.is_approved ? "APPROVED" : "DRAFT"}
              </Badge>
            </div>

            {/* Problem Definition */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" /> 1. Problem Scope & Definition
                </CardTitle>
                <CardDescription>
                  Formalized boundary of the NLP investigation based on primary question.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <textarea
                  className="w-full rounded-md border border-input bg-background p-3 text-sm focus:ring-2 focus:ring-primary focus:outline-none"
                  rows={3}
                  value={editedPlan.problem_definition}
                  onChange={(e) => setEditedPlan({ ...editedPlan, problem_definition: e.target.value })}
                />
              </CardContent>
            </Card>

            {/* Research Subquestions */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Layers className="h-4 w-4 text-primary" /> 2. Research Sub-Questions
                </CardTitle>
                <CardDescription>
                  Decomposed sub-investigations to evaluate in literature.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {editedPlan.sub_questions.map((subQ, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-xs flex items-center justify-center font-bold">
                      {idx + 1}
                    </span>
                    <Input
                      className="text-sm"
                      value={subQ}
                      onChange={(e) => {
                        const updated = [...editedPlan.sub_questions];
                        updated[idx] = e.target.value;
                        setEditedPlan({ ...editedPlan, sub_questions: updated });
                      }}
                    />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Criteria */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold text-emerald-600 flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4" /> Inclusion Criteria
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-1.5 text-xs text-muted-foreground">
                  {editedPlan.inclusion_criteria.map((c, i) => (
                    <div key={i} className="p-2 rounded bg-emerald-500/5 border border-emerald-500/20 text-foreground">
                      {c}
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold text-rose-600 flex items-center gap-1.5">
                    <AlertCircle className="h-4 w-4" /> Exclusion Criteria
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-1.5 text-xs text-muted-foreground">
                  {editedPlan.exclusion_criteria.map((c, i) => (
                    <div key={i} className="p-2 rounded bg-rose-500/5 border border-rose-500/20 text-foreground">
                      {c}
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Potential Experiments */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <FlaskConical className="h-4 w-4 text-primary" /> Potential Experiment Designs
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {editedPlan.potential_experiments.map((exp, idx) => (
                  <div key={idx} className="p-3 rounded-lg border bg-accent/20 text-sm flex items-start gap-2">
                    <span className="font-semibold text-primary">Exp {idx + 1}:</span>
                    <span>{exp}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Right Sidebar: Parameters & Strategy */}
          <div className="space-y-6">
            {/* Search Queries */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <ListFilter className="h-4 w-4 text-primary" /> Search Strategy Queries
                </CardTitle>
                <CardDescription className="text-xs">
                  Sent to Semantic Scholar, arXiv, and OpenAlex.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {editedPlan.search_strategy.map((query, i) => (
                  <div key={i} className="p-2 rounded bg-muted/60 text-xs font-mono border">
                    "{query}"
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Keywords & Concepts */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Keywords & Concepts</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-1.5">
                {editedPlan.keywords.map((kw, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {kw}
                  </Badge>
                ))}
                {editedPlan.related_concepts.map((rc, i) => (
                  <Badge key={i} variant="outline" className="text-xs border-primary/30 text-primary">
                    {rc}
                  </Badge>
                ))}
              </CardContent>
            </Card>

            {/* Candidate Datasets */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" /> Candidate Datasets
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {editedPlan.candidate_datasets.map((ds, i) => (
                  <div key={i} className="flex items-center justify-between text-xs py-1 border-b last:border-0">
                    <span className="font-medium">{ds}</span>
                    <Badge variant="outline" className="text-[10px]">Benchmark</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Metrics */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Gauge className="h-4 w-4 text-primary" /> Target Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-1.5">
                {editedPlan.metrics.map((m, i) => (
                  <Badge key={i} variant="outline" className="text-xs">
                    {m}
                  </Badge>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        <Card className="p-12 text-center">
          <p className="text-muted-foreground">Select a project to view and configure its autonomous research plan.</p>
        </Card>
      )}
    </div>
  );
}
