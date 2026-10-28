import { useSearchParams } from "react-router-dom";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useProjects } from "@/hooks/useProjects";
import { papersApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  BookOpen, ExternalLink, Table as TableIcon,
  Search, FileText
} from "lucide-react";
import { Link } from "react-router-dom";
import { errorMessage } from "@/lib/errors";

export default function LiteraturePage() {
  const { data: projects, isLoading: projectsLoading, error: projectsError } = useProjects({ page_size: 100 });
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedProjectId = searchParams.get("project") || projects?.items[0]?.id || "";
  const [searchFilter, setSearchFilter] = useState<string>("");
  const [discoveryQuery, setDiscoveryQuery] = useState("retrieval augmented generation hallucination");
  const [activeTab, setActiveTab] = useState<"papers" | "matrix">("matrix");

  const { data: papersData, isLoading, error, refetch } = useQuery({
    queryKey: ["papers", selectedProjectId],
    queryFn: () => papersApi.list(selectedProjectId, { page_size: 200 } as any),
    enabled: !!selectedProjectId,
  });

  const papers = papersData?.items || [];

  const filteredPapers = papers.filter((p) =>
    p.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
    p.abstract?.toLowerCase().includes(searchFilter.toLowerCase()) ||
    p.venue?.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const discover = useMutation({
    mutationFn: () => papersApi.discover(selectedProjectId, discoveryQuery.trim()),
    onSuccess: () => refetch(),
  });
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b pb-6">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1 uppercase tracking-wider">
            <BookOpen className="h-4 w-4" /> Academic Literature Discovery & Deep Synthesis
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Literature Explorer</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Deduplicated research papers with metadata, extracted sections, and comparative synthesis matrix.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            className="h-10 rounded-lg border border-input bg-card px-3 py-2 text-sm shadow-sm"
            value={selectedProjectId}
            disabled={projectsLoading || discover.isPending}
            onChange={(e) => {
              const params = new URLSearchParams(searchParams);
              params.set("project", e.target.value);
              setSearchParams(params);
              setSearchFilter("");
              discover.reset();
            }}
          >
            <option value="" disabled>{projectsLoading ? "Loading projects…" : "Select project…"}</option>
            {projects?.items.map((p) => (
              <option key={p.id} value={p.id}>{p.title}</option>
            ))}
          </select>

          {/* Tab switcher */}
          <div className="flex bg-muted p-1 rounded-lg border">
            <button
              onClick={() => setActiveTab("matrix")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === "matrix" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <TableIcon className="h-3.5 w-3.5 inline mr-1" />
              Comparison Matrix
            </button>
            <button
              onClick={() => setActiveTab("papers")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === "papers" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="h-3.5 w-3.5 inline mr-1" />
              Paper Cards ({filteredPapers.length})
            </button>
          </div>
        </div>
      </div>

      {projectsError && <p role="alert" className="text-destructive">Could not load projects: {errorMessage(projectsError)}</p>}
      {!projectsLoading && !projectsError && !projects?.items.length && <p className="text-sm">Create a project to discover and organize papers. <Link to="/projects/new" className="text-primary underline">Create project</Link></p>}
      {/* Filter bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="h-4 w-4 absolute left-3 top-3 text-muted-foreground" />
          <Input
            placeholder="Filter literature by title, abstract, or venue..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); discover.mutate(); }}>
        <Input value={discoveryQuery} onChange={(e) => setDiscoveryQuery(e.target.value)} placeholder="Academic discovery query" />
        <Button disabled={!selectedProjectId || discoveryQuery.trim().length < 3 || discover.isPending}> {discover.isPending ? "Discovering…" : "Discover Papers"}</Button>
      </form>
      {(error || discover.error) && <p role="alert" className="text-destructive">{errorMessage(error || discover.error)}</p>}
      {discover.data && <p className="text-sm">Added {discover.data.added} papers; skipped {discover.data.skipped} duplicates.</p>}
      {projectsLoading || (isLoading && !!selectedProjectId) ? (
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : activeTab === "matrix" ? (
        /* Literature Comparison Matrix (Module H) */
        <Card className="shadow-sm overflow-hidden">
          <CardHeader className="bg-muted/30 border-b">
            <CardTitle className="text-base flex items-center justify-between">
              <span className="flex items-center gap-2">
                <TableIcon className="h-4 w-4 text-primary" /> Literature Synthesis Matrix
              </span>
              <Badge variant="outline" className="text-xs">
                {filteredPapers.length} Papers
              </Badge>
            </CardTitle>
            <CardDescription className="text-xs">
              Methods, datasets, and metrics are extracted mentions. Abstract excerpts are source text; missing information is marked explicitly.
            </CardDescription>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b bg-muted/50 text-xs font-semibold text-muted-foreground">
                  <th className="p-3.5 min-w-[200px]">Paper</th>
                  <th className="p-3.5 min-w-[130px]">Primary Method</th>
                  <th className="p-3.5 min-w-[140px]">Evaluated Datasets</th>
                  <th className="p-3.5 min-w-[110px]">Key Metrics</th>
                  <th className="p-3.5 min-w-[220px]">Source Abstract Excerpt</th>
                  <th className="p-3.5 min-w-[200px]">Limitation</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredPapers.map((paper) => {
                  const extracted = paper.raw_metadata?.extracted_entities || {};
                  const method = (extracted.METHOD || []).join(", ") || "Not extracted";
                  const datasets = (extracted.DATASET || []).join(", ") || "Not extracted";
                  const metric = (extracted.METRIC || []).join(", ") || "Not extracted";
                  const result = paper.abstract ? paper.abstract.slice(0, 240) + (paper.abstract.length > 240 ? "?" : "") : "No abstract available";
                  const limitation = paper.raw_metadata?.limitation_excerpt || "Not extracted from source";

                  return (
                    <tr key={paper.id} className="hover:bg-muted/40 transition-colors">
                      <td className="p-3.5">
                        <div className="font-semibold text-foreground leading-snug"><Link className="hover:underline" to={`/projects/${selectedProjectId}/papers/${paper.id}`}>{paper.title}</Link></div>
                        <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                          <span>{paper.year || "Unknown"}</span>
                          <span>·</span>
                          <span className="truncate max-w-[150px]">{paper.venue || "Unknown venue"}</span>
                          {paper.doi && (
                            <a
                              href={`https://doi.org/${paper.doi}`}
                              target="_blank"
                              rel="noreferrer"
                              className="text-primary hover:underline flex items-center gap-0.5"
                            >
                              DOI <ExternalLink className="h-2.5 w-2.5" />
                            </a>
                          )}
                        </div>
                      </td>
                      <td className="p-3.5">
                        <Badge variant="secondary" className="font-mono text-xs">
                          {method}
                        </Badge>
                      </td>
                      <td className="p-3.5 text-xs text-muted-foreground">
                        {datasets}
                      </td>
                      <td className="p-3.5">
                        <Badge variant="outline" className="text-xs">
                          {metric}
                        </Badge>
                      </td>
                      <td className="p-3.5 text-xs text-foreground/90 leading-relaxed">
                        {result}
                      </td>
                      <td className="p-3.5 text-xs text-amber-700 dark:text-amber-300">
                        {limitation}
                      </td>
                    </tr>
                  );
                })}
                {filteredPapers.length === 0 && (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-muted-foreground text-sm">
                      {!selectedProjectId ? "Create a project to start discovering papers." : papers.length === 0 ? "This project has no papers yet. Use Discover Papers above or upload a PDF on Dashboard." : "No papers match this filter. Clear the filter to show your project papers."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        /* Paper Cards View */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredPapers.map((paper) => (
            <Card key={paper.id} className="shadow-sm hover:border-primary/50 transition-colors">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-3">
                  <CardTitle className="text-base font-semibold leading-snug line-clamp-2">
                    {paper.title}
                  </CardTitle>
                  <Badge variant="outline" className="text-xs shrink-0">
                    {paper.year || "Unknown"}
                  </Badge>
                </div>
                <CardDescription className="text-xs">
                  {paper.authors?.slice(0, 3).map((a) => a.name).join(", ")}
                  {paper.authors?.length > 3 && " et al."}
                  {paper.venue && ` · ${paper.venue}`}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground line-clamp-3">
                  {paper.abstract || "No abstract extracted for this document."}
                </p>
                <div className="flex items-center justify-between pt-2 border-t text-xs">
                  <span className="text-muted-foreground">
                    Citations: <strong className="text-foreground">{paper.citation_count || 0}</strong>
                  </span>
                  <div className="flex gap-2">
                    {paper.doi && (
                      <a
                        href={`https://doi.org/${paper.doi}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary hover:underline flex items-center gap-1"
                      >
                        DOI <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
