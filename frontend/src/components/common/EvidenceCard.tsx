/**
 * EvidenceCard — displays a single evidence snippet with full provenance.
 * Shows paper title, authors, year, page, section, and all retrieval scores.
 */
import { ExternalLink, FileText, BarChart2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { EvidenceSnippet } from "@/types";
import { truncate } from "@/lib/utils";

interface EvidenceCardProps {
  evidence: EvidenceSnippet;
  rank: number;
}

export function EvidenceCard({ evidence, rank }: EvidenceCardProps) {
  return (
    <Card className="relative">
      <div className="absolute top-3 right-3 flex items-center gap-1">
        <Badge variant="outline" className="text-xs font-mono">
          #{rank} · {(evidence.final_score * 100).toFixed(1)}
        </Badge>
      </div>
      <CardHeader className="pb-2 pr-24">
        <p className="text-sm font-medium leading-snug">{evidence.paper_title}</p>
        <p className="text-xs text-muted-foreground">
          {evidence.authors.slice(0, 3).join(", ")}
          {evidence.authors.length > 3 && " et al."}
          {evidence.year && ` · ${evidence.year}`}
          {evidence.doi && (
            <a
              href={`https://doi.org/${evidence.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-1 inline-flex items-center gap-0.5 text-primary hover:underline"
            >
              <ExternalLink className="h-3 w-3" />
              DOI
            </a>
          )}
        </p>
        {(evidence.section_title || evidence.page_number) && (
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <FileText className="h-3 w-3" />
            {evidence.section_title && <span>{evidence.section_title}</span>}
            {evidence.page_number && <span>p. {evidence.page_number}</span>}
          </p>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        <blockquote className="border-l-2 border-primary/30 pl-3 text-sm text-muted-foreground italic">
          "{truncate(evidence.content, 400)}"
        </blockquote>
        {/* Score breakdown */}
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <BarChart2 className="h-3 w-3" />
            Dense: {((evidence.dense_score ?? 0) * 100).toFixed(1)}
          </span>
          <span>BM25: {((evidence.bm25_score ?? 0) * 100).toFixed(1)}</span>
          <span className="font-medium text-foreground">Final: {(evidence.final_score * 100).toFixed(1)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
