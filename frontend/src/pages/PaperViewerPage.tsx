import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { papersApi, retrievalApi, knowledgeApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  FileText, ExternalLink, Calendar, Users, Award, BookOpen,
  Search, ShieldCheck, ArrowLeft, Layers, MessageSquare, Loader2
} from "lucide-react";
import type { EvidenceSnippet } from "@/types";

export default function PaperViewerPage() {
  const { projectId, paperId } = useParams<{ projectId: string; paperId: string }>();
  const [qaQuery, setQaQuery] = useState("");
  const [qaResults, setQaResults] = useState<EvidenceSnippet[] | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const { data: paper, isLoading: paperLoading } = useQuery({
    queryKey: ["paper", projectId, paperId],
    queryFn: () => papersApi.get(projectId!, paperId!),
    enabled: !!projectId && !!paperId,
  });

  const { data: entities } = useQuery({
    queryKey: ["knowledge", projectId, "entities"],
    queryFn: () => knowledgeApi.listEntities(projectId!, { page_size: 100 } as any),
    enabled: !!projectId,
  });

  const { data: claims } = useQuery({
    queryKey: ["knowledge", projectId, "claims"],
    queryFn: () => knowledgeApi.listClaims(projectId!),
    enabled: !!projectId,
  });

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qaQuery.trim() || !projectId) return;
    setIsSearching(true);
    try {
      const res = await retrievalApi.search({
        query: qaQuery,
        project_id: projectId,
        top_k: 5,
        use_reranking: true,
      });
      setQaResults(res.evidence);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  if (paperLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="p-8 text-center space-y-4">
        <p className="text-muted-foreground">Paper not found.</p>
        <Link to={`/projects/${projectId}`}>
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" /> Back to Project
          </Button>
        </Link>
      </div>
    );
  }

  // Filter entities mentioned in this paper or related
  const paperEntities = entities?.items?.filter((e: any) => e.paper_id === paperId) || entities?.items?.slice(0, 10) || [];

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Back button & Breadcrumb */}
      <div className="flex items-center gap-3">
        <Link to="/literature">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-muted-foreground">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Literature Explorer
          </Button>
        </Link>
      </div>

      {/* Main Header Card */}
      <Card className="border-border shadow-sm">
        <CardContent className="p-6 space-y-4">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-2">
                <Badge variant={paper.status === "processed" ? "success" : "secondary"}>
                  {paper.status}
                </Badge>
                {paper.venue && (
                  <Badge variant="outline" className="font-mono text-xs">
                    {paper.venue}
                  </Badge>
                )}
                {paper.year && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Calendar className="h-3 w-3" /> {paper.year}
                  </span>
                )}
              </div>

              <h1 className="text-2xl font-bold leading-tight text-foreground">
                {paper.title}
              </h1>

              {paper.authors && paper.authors.length > 0 && (
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Users className="h-3.5 w-3.5" />
                  <span>
                    {paper.authors.map((a) => (typeof a === "string" ? a : a.name)).join(", ")}
                  </span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap md:flex-col gap-2 shrink-0">
              {paper.arxiv_id && (
                <a
                  href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex"
                >
                  <Button variant="outline" size="sm" className="gap-1 text-xs w-full">
                    <ExternalLink className="h-3.5 w-3.5" /> arXiv:{paper.arxiv_id}
                  </Button>
                </a>
              )}
              {paper.doi && (
                <a
                  href={`https://doi.org/${paper.doi}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex"
                >
                  <Button variant="outline" size="sm" className="gap-1 text-xs w-full">
                    <ExternalLink className="h-3.5 w-3.5" /> DOI
                  </Button>
                </a>
              )}
            </div>
          </div>

          {/* Abstract */}
          {paper.abstract && (
            <div className="pt-4 border-t">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                <BookOpen className="h-3.5 w-3.5" /> Abstract
              </h3>
              <p className="text-sm leading-relaxed text-foreground/90 bg-muted/20 p-4 rounded-lg border border-border/50">
                {paper.abstract}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Grid: Extracted Knowledge & Grounded Q&A */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Knowledge Graph Entities & Claims */}
        <div className="lg:col-span-1 space-y-6">
          {/* Extracted Entities */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Layers className="h-4 w-4 text-primary" />
                Extracted NLP Entities
              </CardTitle>
              <CardDescription className="text-xs">
                Models, benchmarks, metrics and tasks discovered in this paper.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {paperEntities.length === 0 ? (
                <p className="text-xs text-muted-foreground">No entities extracted yet.</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {paperEntities.map((ent: any, idx: number) => (
                    <Badge key={idx} variant="secondary" className="text-xs py-1 px-2">
                      <span className="font-semibold text-primary mr-1">[{ent.entity_type}]</span>
                      {ent.name}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Core Verified Claims */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                Ground-Truth Claims
              </CardTitle>
              <CardDescription className="text-xs">
                Extracted claims verified against verbatim paper chunks.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {!claims?.items?.length ? (
                <p className="text-xs text-muted-foreground">No claims extracted yet.</p>
              ) : (
                claims.items.slice(0, 4).map((c) => (
                  <div key={c.id} className="p-2.5 rounded-lg border bg-muted/10 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <Badge variant="success" className="text-[10px]">
                        {c.verification_status}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {c.artifact_type}
                      </span>
                    </div>
                    <p className="text-xs text-foreground/90 leading-normal">
                      {c.claim_text}
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Evidence-Grounded Q&A */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-primary" />
                Evidence-Grounded Paper Q&A
              </CardTitle>
              <CardDescription className="text-xs">
                Query this paper and retrieve verbatim evidence chunks with dense + BM25 hybrid ranking scores.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleAsk} className="flex gap-2">
                <Input
                  placeholder="e.g. What were the exact Exact Match results on PopQA vs TriviaQA?"
                  value={qaQuery}
                  onChange={(e) => setQaQuery(e.target.value)}
                  className="text-xs"
                />
                <Button type="submit" size="sm" disabled={isSearching} className="gap-1.5 shrink-0">
                  {isSearching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
                  Ask Paper
                </Button>
              </form>

              {/* Q&A Evidence Results */}
              <div className="space-y-3 mt-4">
                {qaResults === null ? (
                  <div className="py-8 text-center text-xs text-muted-foreground border rounded-lg bg-muted/10">
                    Ask a technical question above to inspect grounded passages, section anchors, and BM25/Dense provenance.
                  </div>
                ) : qaResults.length === 0 ? (
                  <div className="py-6 text-center text-xs text-muted-foreground">
                    No matching passages found for this query.
                  </div>
                ) : (
                  qaResults.map((snippet, idx) => (
                    <div key={idx} className="p-4 rounded-xl border bg-card space-y-2 shadow-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-primary">
                          Section: {snippet.section_title || "Body Passage"}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-mono bg-muted px-2 py-0.5 rounded text-muted-foreground">
                            Score: {(snippet.final_score * 100).toFixed(1)}%
                          </span>
                          {snippet.page_number && (
                            <span className="text-[11px] text-muted-foreground">
                              p. {snippet.page_number}
                            </span>
                          )}
                        </div>
                      </div>
                      <blockquote className="text-xs italic bg-muted/30 p-3 rounded border-l-2 border-primary text-foreground/90 leading-relaxed font-serif">
                        "{snippet.content}"
                      </blockquote>
                      <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
                        <span>Chunk: {snippet.chunk_id.slice(0, 8)}</span>
                        <span>Dense: {snippet.dense_score?.toFixed(2) ?? "—"} | BM25: {snippet.bm25_score?.toFixed(2) ?? "—"}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
