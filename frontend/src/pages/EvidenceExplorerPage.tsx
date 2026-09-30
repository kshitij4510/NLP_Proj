import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useProjects } from "@/hooks/useProjects";
import { knowledgeApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  ShieldCheck, CheckCircle2, AlertTriangle, XCircle, HelpCircle,
  Search, BookOpen, Quote, FileText, ArrowRight
} from "lucide-react";
import type { Claim } from "@/types";

const STATUS_ICONS: Record<string, any> = {
  SUPPORTED: CheckCircle2,
  PARTIALLY_SUPPORTED: AlertTriangle,
  CONTRADICTED: XCircle,
  INSUFFICIENT_EVIDENCE: HelpCircle,
};

const STATUS_COLORS: Record<string, string> = {
  SUPPORTED: "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-800",
  PARTIALLY_SUPPORTED: "bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800",
  CONTRADICTED: "bg-rose-50 text-rose-800 border-rose-300 dark:bg-rose-950/40 dark:text-rose-200 dark:border-rose-800",
  INSUFFICIENT_EVIDENCE: "bg-slate-50 text-slate-800 border-slate-300 dark:bg-slate-900/40 dark:text-slate-200 dark:border-slate-700",
};

export default function EvidenceExplorerPage() {
  const { data: projects } = useProjects({ page_size: 50 });
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchFilter, setSearchFilter] = useState<string>("");

  const { data: claimsData, isLoading } = useQuery({
    queryKey: ["claims", selectedProjectId],
    queryFn: () => knowledgeApi.listClaims(selectedProjectId),
    enabled: !!selectedProjectId,
  });

  const claims = claimsData?.items || [];

  const filteredClaims = claims.filter((c) => {
    const matchesStatus = statusFilter === "ALL" || c.verification_status === statusFilter;
    const matchesText = c.claim_text.toLowerCase().includes(searchFilter.toLowerCase());
    return matchesStatus && matchesText;
  });

  const counts = {
    ALL: claims.length,
    SUPPORTED: claims.filter((c) => c.verification_status === "SUPPORTED").length,
    PARTIALLY_SUPPORTED: claims.filter((c) => c.verification_status === "PARTIALLY_SUPPORTED").length,
    CONTRADICTED: claims.filter((c) => c.verification_status === "CONTRADICTED").length,
    INSUFFICIENT_EVIDENCE: claims.filter((c) => c.verification_status === "INSUFFICIENT_EVIDENCE").length,
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b pb-6">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1 uppercase tracking-wider">
            <ShieldCheck className="h-4 w-4" /> Traceable Claim Verification (Module N & §27)
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Evidence Explorer</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Audit every scientific claim against extracted document passages. No ungrounded conclusions.
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

      {/* Filters & Status Tabs */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Status Pills */}
        <div className="flex flex-wrap gap-2 w-full sm:w-auto">
          {[
            { id: "ALL", label: "All Claims", count: counts.ALL },
            { id: "SUPPORTED", label: "Supported", count: counts.SUPPORTED },
            { id: "PARTIALLY_SUPPORTED", label: "Partially", count: counts.PARTIALLY_SUPPORTED },
            { id: "CONTRADICTED", label: "Contradicted", count: counts.CONTRADICTED },
            { id: "INSUFFICIENT_EVIDENCE", label: "Insufficient", count: counts.INSUFFICIENT_EVIDENCE },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all flex items-center gap-1.5 ${
                statusFilter === tab.id
                  ? "bg-primary text-primary-foreground border-primary shadow-sm"
                  : "bg-card text-muted-foreground hover:bg-accent"
              }`}
            >
              <span>{tab.label}</span>
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                statusFilter === tab.id ? "bg-primary-foreground/20 text-primary-foreground" : "bg-muted text-muted-foreground"
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="h-4 w-4 absolute left-3 top-3 text-muted-foreground" />
          <Input
            placeholder="Search claims..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="pl-9 h-9 text-xs"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : filteredClaims.length > 0 ? (
        <div className="space-y-4">
          {filteredClaims.map((claim) => {
            const Icon = STATUS_ICONS[claim.verification_status] || HelpCircle;
            const badgeClass = STATUS_COLORS[claim.verification_status] || "";

            return (
              <Card key={claim.id} className="shadow-sm border overflow-hidden">
                <CardHeader className="bg-muted/20 pb-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border flex items-center gap-1.5 ${badgeClass}`}>
                        <Icon className="h-3.5 w-3.5" />
                        {claim.verification_status.replace("_", " ")}
                      </span>
                      {claim.confidence && (
                        <span className="text-xs text-muted-foreground">
                          Confidence: <strong>{(claim.confidence * 100).toFixed(0)}%</strong>
                        </span>
                      )}
                    </div>
                    <Badge variant="outline" className="text-[10px] w-fit font-mono">
                      {claim.artifact_type}
                    </Badge>
                  </div>

                  <CardTitle className="text-base font-semibold mt-2 text-foreground leading-snug">
                    "{claim.claim_text}"
                  </CardTitle>
                </CardHeader>

                <CardContent className="pt-4 space-y-3">
                  {claim.evidence_links && claim.evidence_links.length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Grounding Evidence ({claim.evidence_links.length} source passages):
                      </p>
                      {claim.evidence_links.map((link) => (
                        <div key={link.id} className="p-3.5 rounded-lg border bg-accent/10 space-y-2 text-xs">
                          <div className="flex items-center justify-between text-muted-foreground border-b pb-1.5">
                            <span className="font-medium flex items-center gap-1">
                              <BookOpen className="h-3 w-3" />
                              Section: {link.section_title || "Body"} · Page {link.page_number || 1}
                            </span>
                            <span className="font-mono">
                              Similarity: {(link.relevance_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="italic text-foreground/90 pl-3 border-l-2 border-primary">
                            "{link.evidence_snippet}"
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 rounded-lg border border-dashed text-xs text-muted-foreground flex items-center gap-2">
                      <HelpCircle className="h-4 w-4 text-slate-400" />
                      <span>No specific grounding passage mapped yet. Status verified via synthesis pass.</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="p-12 text-center text-muted-foreground">
          <p>No claims found matching the current filter. Select another project or run claim verification.</p>
        </Card>
      )}
    </div>
  );
}
