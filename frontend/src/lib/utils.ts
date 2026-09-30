import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "…";
}

export function formatScore(score: number): string {
  return (score * 100).toFixed(1) + "%";
}

export const PIPELINE_STAGES = [
  "PLANNING", "DISCOVERY", "INGESTION", "ANALYSIS", "EXTRACTION",
  "SYNTHESIS", "GAP_ANALYSIS", "HYPOTHESIS", "EXPERIMENT_DESIGN",
  "VERIFICATION", "REPORTING", "COMPLETED",
] as const;

export function pipelineProgress(stage: string): number {
  const idx = PIPELINE_STAGES.indexOf(stage as any);
  if (idx < 0) return 0;
  return ((idx + 1) / PIPELINE_STAGES.length) * 100;
}

export const STATUS_COLORS: Record<string, string> = {
  created: "bg-gray-100 text-gray-700",
  planning: "bg-blue-100 text-blue-700",
  active: "bg-green-100 text-green-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
  running: "bg-yellow-100 text-yellow-700",
  pending: "bg-gray-100 text-gray-700",
  SUPPORTED: "bg-green-100 text-green-700",
  PARTIALLY_SUPPORTED: "bg-yellow-100 text-yellow-700",
  CONTRADICTED: "bg-red-100 text-red-700",
  INSUFFICIENT_EVIDENCE: "bg-gray-100 text-gray-700",
};
