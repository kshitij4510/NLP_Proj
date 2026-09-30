import { useParams, Link } from "react-router-dom";
import { useProject, useProjectSummary, useTriggerPipeline } from "@/hooks/useProjects";
import { useActiveJob } from "@/hooks/useJobs";
import { usePapers } from "@/hooks/usePapers";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PipelineStatus } from "@/components/common/PipelineStatus";
import { Loader2, Play, FileText, BookOpen, Lightbulb, FlaskConical, ArrowLeft } from "lucide-react";
import { formatDate, STATUS_COLORS } from "@/lib/utils";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: project, isLoading } = useProject(id!);
  const { data: summary } = useProjectSummary(id!);
  const { data: activeJob } = useActiveJob(id!);
  const { data: papersData } = usePapers(id!, { page_size: 5 } as any);
  const triggerPipeline = useTriggerPipeline(id!);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }
  if (!project) return <div className="p-8 text-muted-foreground">Project not found.</div>;

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link to="/projects" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2">
            <ArrowLeft className="h-3 w-3" /> Projects
          </Link>
          <h1 className="text-2xl font-bold">{project.title}</h1>
          {project.description && <p className="text-muted-foreground mt-1">{project.description}</p>}
          <div className="flex items-center gap-2 mt-2">
            <Badge className={STATUS_COLORS[project.status]}>{project.status}</Badge>
            <span className="text-xs text-muted-foreground">Updated {formatDate(project.updated_at)}</span>
          </div>
        </div>
        <Button
          onClick={() => triggerPipeline.mutate(undefined)}
          disabled={triggerPipeline.isPending || activeJob?.status === "running"}
        >
          {triggerPipeline.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Play className="mr-2 h-4 w-4" />
          )}
          Run Pipeline
        </Button>
      </div>

      {/* Research question */}
      {project.research_questions?.[0] && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="p-4">
            <p className="text-xs font-medium text-primary mb-1 uppercase tracking-wide">Research Question</p>
            <p className="text-sm font-medium">{project.research_questions[0].question}</p>
          </CardContent>
        </Card>
      )}

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Papers", value: summary?.papers ?? project.paper_count, icon: BookOpen },
          { label: "Gaps", value: summary?.research_gaps ?? 0, icon: FileText },
          { label: "Hypotheses", value: summary?.hypotheses ?? project.hypothesis_count, icon: Lightbulb },
          { label: "Experiments", value: summary?.experiments ?? project.experiment_count, icon: FlaskConical },
        ].map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="flex items-center gap-3 p-4">
              <Icon className="h-6 w-6 text-muted-foreground" />
              <div>
                <p className="text-xl font-bold">{value}</p>
                <p className="text-xs text-muted-foreground">{label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pipeline status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pipeline Status</CardTitle>
        </CardHeader>
        <CardContent>
          <PipelineStatus job={activeJob} />
        </CardContent>
      </Card>

      {/* Recent papers */}
      {papersData && papersData.total > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base">Papers ({papersData.total})</CardTitle>
            <Link to={`/projects/${id}/papers`} className="text-sm text-primary hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {papersData.items.map((paper) => (
                <div key={paper.id} className="flex items-start justify-between py-2 border-b last:border-0">
                  <div>
                    <p className="text-sm font-medium line-clamp-1">{paper.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {paper.authors.slice(0, 2).map((a) => a.name).join(", ")}
                      {paper.year && ` · ${paper.year}`}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-xs ml-2 shrink-0">{paper.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
