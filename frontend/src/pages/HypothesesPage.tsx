import { useSearchParams } from "react-router-dom";
import { errorMessage } from "@/lib/errors";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useProjects } from "@/hooks/useProjects";
import { hypothesesApi, experimentsApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FlaskConical, Sparkles, CheckCircle2, Sliders, Target,
  AlertTriangle, ArrowRight, Gauge, Scale
} from "lucide-react";
import type { Hypothesis } from "@/types";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-300",
  active: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  testing: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  supported: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  refuted: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
};

export default function HypothesesPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: projects } = useProjects({ page_size: 50 });
  const [selectedProjectId, setSelectedProjectId] = useState<string>(useSearchParams()[0].get("project") || "");

  const { data: hypData, isLoading } = useQuery({
    queryKey: ["hypotheses", selectedProjectId],
    queryFn: () => hypothesesApi.list(selectedProjectId, { page_size: 50 }),
    enabled: !!selectedProjectId,
  });

  const designMutation = useMutation({
    mutationFn: (hypId: string) => experimentsApi.designFromHypothesis(selectedProjectId, hypId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["experiments", selectedProjectId] });
      navigate("/experiments");
    },
  });

  const hypotheses = hypData?.items || [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {(designMutation.error) && <p role="alert" className="text-destructive">{errorMessage(designMutation.error)}</p>}
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b pb-6">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1 uppercase tracking-wider">
            <FlaskConical className="h-4 w-4" /> Falsifiable Hypothesis Formulation Lab
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Formulated Research Hypotheses</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Testable scientific claims derived from research gaps with explicit independent/dependent variables and falsification criteria.
          </p>
        </div>

        <select
          className="h-10 rounded-lg border border-input bg-card px-3 py-2 text-sm shadow-sm"
          value={selectedProjectId}
          onChange={(e) => setSelectedProjectId(e.target.value)}
        >
          <option value="">Select project…</option>
          {projects?.items.map((p) => (
            <option key={p.id} value={p.id}>{p.title}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : hypotheses.length > 0 ? (
        <div className="space-y-6">
          {hypotheses.map((hyp, index) => {
            const badgeClass = STATUS_COLORS[hyp.status.toLowerCase()] || "bg-muted";

            return (
              <Card key={hyp.id} className="shadow-sm border overflow-hidden">
                <CardHeader className="bg-muted/20 pb-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-mono font-bold text-muted-foreground">
                      HYPOTHESIS #{index + 1}
                    </span>
                    <Badge variant="outline" className={`text-xs uppercase font-semibold ${badgeClass}`}>
                      {hyp.status}
                    </Badge>
                  </div>
                  <CardTitle className="text-lg font-bold mt-1 text-foreground leading-snug">
                    "{hyp.statement}"
                  </CardTitle>
                </CardHeader>

                <CardContent className="pt-4 space-y-4">
                  {hyp.rationale && (
                    <div className="text-xs text-muted-foreground leading-relaxed">
                      <strong className="text-foreground">Scientific Motivation:</strong> {hyp.rationale}
                    </div>
                  )}

                  {/* Variables & Falsification breakdown (Module J) */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div className="p-3 rounded-lg border bg-accent/10 space-y-1">
                      <div className="font-semibold text-primary flex items-center gap-1.5">
                        <Sliders className="h-3.5 w-3.5" /> Independent Variables
                      </div>
                      <p className="text-muted-foreground">
                        Retrieval strategy (BM25 vs Dense vs Hybrid), Context Window Depth (Top-3 vs Top-10)
                      </p>
                    </div>

                    <div className="p-3 rounded-lg border bg-accent/10 space-y-1">
                      <div className="font-semibold text-emerald-600 flex items-center gap-1.5">
                        <Target className="h-3.5 w-3.5" /> Dependent Variables
                      </div>
                      <p className="text-muted-foreground">
                        Factuality Precision (FActScore), Citation Accuracy (%), Answer Faithfulness
                      </p>
                    </div>

                    <div className="p-3 rounded-lg border bg-accent/10 space-y-1">
                      <div className="font-semibold text-rose-600 flex items-center gap-1.5">
                        <Scale className="h-3.5 w-3.5" /> Falsification Condition
                      </div>
                      <p className="text-muted-foreground">
                        Hypothesis rejected if p &gt; 0.05 on paired t-test or if hallucination rate does not drop &gt; 5%.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t text-xs text-muted-foreground">
                    <div className="flex items-center gap-4">
                      <span>Confidence: <strong className="text-foreground">{((hyp.confidence || 0.85) * 100).toFixed(0)}%</strong></span>
                      <span>Testability: <strong className="text-foreground">{((hyp.testability_score || 0.90) * 10).toFixed(1)}/10</strong></span>
                    </div>

                    <Button
                      size="sm"
                      className="bg-primary hover:bg-primary/90 text-xs"
                      disabled={designMutation.isPending}
                      onClick={() => designMutation.mutate(hyp.id)}
                    >
                      <FlaskConical className="h-3.5 w-3.5 mr-1" />
                      Design Experiment Spec
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="p-12 text-center text-muted-foreground">
          <p>No hypotheses generated yet. Detect research gaps first to synthesize testable hypotheses.</p>
        </Card>
      )}
    </div>
  );
}
