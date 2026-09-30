import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useProjects } from "@/hooks/useProjects";
import { retrievalApi } from "@/api/endpoints";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { EvidenceCard } from "@/components/common/EvidenceCard";
import { Loader2, Search } from "lucide-react";
import type { RetrievalResult } from "@/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [selectedProject, setSelectedProject] = useState("");
  const { data: projects } = useProjects({ page_size: 50 });

  const search = useMutation({
    mutationFn: () =>
      retrievalApi.search({
        query,
        project_id: selectedProject,
        top_k: 10,
        use_reranking: true,
      }),
  });

  const result = search.data as RetrievalResult | undefined;

  return (
    <div className="p-8 space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">Evidence Search</h1>
        <p className="text-muted-foreground mt-1">
          Hybrid BM25 + dense retrieval over your paper corpus.
          Every result includes source, page, and score breakdown.
        </p>
      </div>

      {/* Search form */}
      <Card>
        <CardContent className="p-4 space-y-3">
          <div className="flex gap-3">
            <select
              className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
            >
              <option value="">Select project…</option>
              {projects?.items.map((p) => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Enter your research query…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && selectedProject && query && search.mutate()}
              className="flex-1"
            />
            <Button
              onClick={() => search.mutate()}
              disabled={!query || !selectedProject || search.isPending}
            >
              {search.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>{result.evidence.length} results from {result.total_candidates} candidates</span>
            <span>{result.retrieval_time_ms.toFixed(0)}ms · {result.reranked ? "reranked" : "not reranked"}</span>
          </div>
          {result.evidence.map((e, i) => (
            <EvidenceCard key={e.chunk_id} evidence={e} rank={i + 1} />
          ))}
          {result.evidence.length === 0 && (
            <p className="text-center text-muted-foreground py-8">
              No evidence found. Make sure papers are ingested and embeddings are computed.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
