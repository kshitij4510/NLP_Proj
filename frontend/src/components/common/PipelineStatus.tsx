/**
 * Pipeline stage progress tracker.
 * Shows each stage with status indicator and current progress bar.
 */
import { CheckCircle2, Circle, AlertCircle, Loader2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import type { Job } from "@/types";
import { PIPELINE_STAGES } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface PipelineStatusProps {
  job: Job | null | undefined;
}

const STAGE_LABELS: Record<string, string> = {
  PLANNING: "Planning",
  DISCOVERY: "Discovery",
  INGESTION: "Ingestion",
  ANALYSIS: "Analysis",
  EXTRACTION: "Extraction",
  SYNTHESIS: "Synthesis",
  GAP_ANALYSIS: "Gap Analysis",
  HYPOTHESIS: "Hypotheses",
  EXPERIMENT_DESIGN: "Experiment Design",
  VERIFICATION: "Verification",
  REPORTING: "Reporting",
  COMPLETED: "Completed",
};

export function PipelineStatus({ job }: PipelineStatusProps) {
  if (!job) {
    return (
      <div className="text-sm text-muted-foreground p-4">
        No active pipeline. Trigger a run to start.
      </div>
    );
  }

  const currentIdx = PIPELINE_STAGES.indexOf(job.stage as any);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {job.status === "running" && <Loader2 className="h-4 w-4 animate-spin text-blue-500" />}
          {job.status === "completed" && <CheckCircle2 className="h-4 w-4 text-green-500" />}
          {job.status === "failed" && <AlertCircle className="h-4 w-4 text-red-500" />}
          <span className="font-medium">{STAGE_LABELS[job.stage] ?? job.stage}</span>
        </div>
        <Badge variant={job.status === "completed" ? "success" : job.status === "failed" ? "destructive" : "default"}>
          {job.status}
        </Badge>
      </div>

      <Progress value={job.progress * 100} className="h-2" />

      <div className="grid grid-cols-4 gap-1 sm:grid-cols-6">
        {PIPELINE_STAGES.filter((s) => s !== "COMPLETED").map((stage, idx) => {
          const done = idx < currentIdx;
          const active = idx === currentIdx;
          return (
            <div
              key={stage}
              className={cn(
                "flex flex-col items-center gap-1 text-center",
                done && "text-green-600",
                active && "text-blue-600",
                !done && !active && "text-muted-foreground"
              )}
            >
              <div className="text-xs font-medium leading-tight">{STAGE_LABELS[stage]}</div>
              <div className={cn("h-1.5 w-full rounded", done ? "bg-green-400" : active ? "bg-blue-400" : "bg-gray-200")} />
            </div>
          );
        })}
      </div>

      {job.error_message && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          <strong>Error:</strong> {job.error_message}
        </div>
      )}
    </div>
  );
}
