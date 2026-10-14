import ManuscriptStudio from "@/components/ManuscriptStudio";
import { useSearchParams } from "react-router-dom";
import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useProjects } from "@/hooks/useProjects";
import { reportsApi } from "@/api/endpoints";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Loader2, AlertTriangle } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { errorMessage } from "@/lib/errors";
import type { Report } from "@/types";

export default function ReportsPage() {
  const { data: projects } = useProjects({ page_size: 50 });
  const [selectedProject, setSelectedProject] = useState(useSearchParams()[0].get("project") || "");
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  const { data: reports, refetch } = useQuery({
    queryKey: ["reports", selectedProject],
    queryFn: () => reportsApi.list(selectedProject),
    enabled: !!selectedProject,
  });

  const generate = useMutation({
    mutationFn: () => reportsApi.generate(selectedProject, { verify_claims: true }),
    onSuccess: (report) => { setSelectedReport(report); refetch(); },
  });

  const download = useMutation({
    mutationFn: (format: "ieee" | "markdown" | "bibtex") => reportsApi.download(selectedProject, selectedReport!.id, format),
  });

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Manuscripts</h1>
          <p className="text-muted-foreground mt-1">
            Generate a manuscript from the project corpus, hypotheses, and recorded results. Drafts expose verification limitations.
          </p>
        </div>
      </div>

      <div className="flex gap-3 items-center">
        <select
          className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={selectedProject}
          onChange={(e) => { setSelectedProject(e.target.value); setSelectedReport(null); }}
        >
          <option value="">Select project…</option>
          {projects?.items.map((p) => (
            <option key={p.id} value={p.id}>{p.title}</option>
          ))}
        </select>
        <Button
          onClick={() => generate.mutate()}
          disabled={!selectedProject || generate.isPending}
        >
          {generate.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileText className="mr-2 h-4 w-4" />}
          Create corpus review
        </Button>
      </div>

      <ManuscriptStudio key={selectedProject} projectId={selectedProject} onReport={(report)=>{setSelectedReport(report);refetch();}} />
      {(generate.error || download.error) && <p role="alert" className="text-destructive">{errorMessage(generate.error || download.error)}</p>}
      {selectedReport && <div className="flex gap-2 flex-wrap">
        <Button disabled={download.isPending} onClick={() => download.mutate("ieee")}>Download IEEE Paper (.tex)</Button>
        <Button variant="outline" disabled={download.isPending} onClick={() => download.mutate("markdown")}>Markdown</Button>
        <Button variant="outline" disabled={download.isPending} onClick={() => download.mutate("bibtex")}>BibTeX</Button>
        <p className="text-sm text-muted-foreground w-full">Compile the IEEE source in Overleaf or with IEEEtran installed. Replace author details and review the draft before submission.</p>
      </div>}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Report list */}
        <div className="space-y-3">
          {reports?.items.map((report) => (
            <Card
              key={report.id}
              className={`cursor-pointer hover:shadow-sm transition-shadow ${selectedReport?.id === report.id ? "ring-2 ring-primary" : ""}`}
              onClick={() => setSelectedReport(report)}
            >
              <CardContent className="p-4">
                <p className="font-medium text-sm line-clamp-2">{report.title}</p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant={report.status === "completed" ? "success" : "secondary"} className="text-xs">
                    {report.status}
                  </Badge>
                  {report.unsupported_claim_count > 0 && (
                    <span className="flex items-center gap-1 text-xs text-amber-600">
                      <AlertTriangle className="h-3 w-3" />
                      {report.unsupported_claim_count} unsupported
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-1">{formatDate(report.updated_at)}</p>
              </CardContent>
            </Card>
          ))}
          {reports?.items.length === 0 && selectedProject && (
            <p className="text-sm text-muted-foreground">No reports yet.</p>
          )}
        </div>

        {/* Report viewer */}
        {selectedReport && (
          <div className="lg:col-span-2 space-y-4 max-h-[70vh] overflow-y-auto">
            <h2 className="text-lg font-semibold">{selectedReport.title}</h2>
            {[
              ["Abstract", selectedReport.abstract],
              ["Research Question", selectedReport.research_question_section],
              ["Background", selectedReport.background],
              ["Literature Review", selectedReport.literature_review],
              ["Research Gaps", selectedReport.research_gaps_section],
              ["Hypotheses", selectedReport.hypotheses_section],
              ["Experimental Design", selectedReport.experimental_design],
              ["Results", selectedReport.results],
              ["Limitations", selectedReport.limitations],
              ["Conclusion", selectedReport.conclusion],
            ].map(([section, content]) =>
              content ? (
                <Card key={section as string}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">{section}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground whitespace-pre-wrap">{content as string}</p>
                  </CardContent>
                </Card>
              ) : null
            )}
            {selectedReport.citations.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">References ({selectedReport.citations.filter((c) => c.style === "ieee").length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {selectedReport.citations.filter((c) => c.style === "ieee").map((c) => (
                      <p key={c.id} className="text-xs text-muted-foreground">{c.formatted_citation}</p>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
