import { errorMessage } from "@/lib/errors";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useProjects } from "@/hooks/useProjects";
import { gapsApi, hypothesesApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Lightbulb, AlertCircle, Sparkles, BookOpen, Layers,
  ChevronRight, ArrowRight, CheckCircle2, RefreshCw
} from "lucide-react";
import type { GapType, ResearchGap } from "@/types";

const GAP_TYPE_COLORS: Record<string, string> = {
  methodological: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200 border-blue-300",
  empirical: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200 border-emerald-300",
  theoretical: "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-200 border-purple-300",
  application: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200 border-amber-300",
  replication: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200 border-rose-300",
  data: "bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-200 border-cyan-300",
};

export default function GapsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: projects } = useProjects({ page_size: 50 });
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [selectedGap, setSelectedGap] = useState<ResearchGap | null>(null);

  const { data: gapsData, isLoading, refetch } = useQuery({
    queryKey: ["research-gaps", selectedProjectId],
    queryFn: () => gapsApi.list(selectedProjectId, { page_size: 50 }),
    enabled: !!selectedProjectId,
  });

  const generateHypMutation = useMutation({
    mutationFn: (gapId: string) => hypothesesApi.generateForGap(selectedProjectId, gapId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hypotheses", selectedProjectId] });
      navigate(`/hypotheses?project=${selectedProjectId}`);
    },
  });

  const gaps = gapsData?.items || [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {(generateHypMutation.error) && <p role="alert" className="text-destructive">{errorMessage(generateHypMutation.error)}</p>}
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b pb-6">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1 uppercase tracking-wider">
            <Lightbulb className="h-4 w-4" /> Empirical Research Gap Detection
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Research Gap Explorer</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Uncovered limitations, contradictory findings, and underexplored benchmarks grounded in retrieved evidence.
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
      ) : gaps.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {gaps.map((gap, index) => {
            const badgeClass = GAP_TYPE_COLORS[gap.gap_type.toLowerCase()] || "bg-muted";

            return (
              <Card key={gap.id} className="shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-xs font-mono font-bold text-muted-foreground">
                      POTENTIAL GAP #{index + 1}
                    </span>
                    <Badge variant="outline" className={`text-[10px] uppercase font-semibold ${badgeClass}`}>
                      {gap.gap_type}
                    </Badge>
                  </div>
                  <CardTitle className="text-lg font-bold leading-snug">
                    {gap.title}
                  </CardTitle>
                </CardHeader>

                <CardContent className="space-y-4 flex-1">
                  <p className="text-sm text-foreground/90 leading-relaxed">
                    {gap.description}
                  </p>

                  <div className="p-3 rounded-lg bg-accent/20 border text-xs space-y-1.5">
                    <div className="font-semibold text-primary flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5" /> Why this gap matters:
                    </div>
                    <p className="text-muted-foreground">
                      Resolving this bottleneck enables more faithful zero-shot QA without requiring computationally heavy full fine-tuning.
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t text-xs text-muted-foreground">
                    <span>
                      Importance: <strong className="text-foreground">{((gap.importance_score || 0.85) * 10).toFixed(1)}/10</strong>
                    </span>
                    <span className="font-mono text-[11px]">
                      Detected via {gap.detected_by}
                    </span>
                  </div>
                </CardContent>

                <div className="p-4 pt-0 flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 text-xs"
                    onClick={() => navigate("/evidence")}
                  >
                    <BookOpen className="h-3.5 w-3.5 mr-1" />
                    Explore Evidence
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1 text-xs bg-primary hover:bg-primary/90"
                    disabled={generateHypMutation.isPending}
                    onClick={() => generateHypMutation.mutate(gap.id)}
                  >
                    <Sparkles className="h-3.5 w-3.5 mr-1" />
                    Generate Hypothesis
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="p-12 text-center text-muted-foreground">
          <p>No research gaps detected yet. Run the synthesis stage to analyze retrieved literature.</p>
        </Card>
      )}
    </div>
  );
}
