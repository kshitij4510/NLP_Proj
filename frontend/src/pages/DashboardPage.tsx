import ManuscriptStudio from "@/components/ManuscriptStudio";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useProjects, useProjectSummary } from "@/hooks/useProjects";
import { researchApi } from "@/api/endpoints";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Plus, BookOpen, FlaskConical, FileText, Lightbulb,
  ShieldCheck, ArrowRight, BarChart3, TrendingUp, Layers, Compass
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from "recharts";
import { formatDate, STATUS_COLORS } from "@/lib/utils";

export default function DashboardPage() {
  const { data: projectsData, isLoading: projectsLoading } = useProjects({ page_size: 20 });
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");

  const projects = projectsData?.items || [];
  const effectiveProjectId = selectedProjectId || (projects[0]?.id ?? "");

  const { data: summary } = useProjectSummary(effectiveProjectId);

  const { data: temporalData } = useQuery({
    queryKey: ["research", effectiveProjectId, "temporal"],
    queryFn: () => researchApi.getTemporal(effectiveProjectId),
    enabled: !!effectiveProjectId,
  });

  const timelineChartData = temporalData?.timeline?.map((t) => ({
    year: t.year.toString(),
    papers: t.paper_count,
    models: t.top_models.length,
    datasets: t.top_datasets.length,
  })) || [];

  const modelChartData = temporalData?.model_evolution?.slice(0, 7).map((m) => {
    const totalMentions = Object.values(m.counts || {}).reduce((a, b) => a + b, 0);
    return { name: m.name, mentions: totalMentions };
  }) || [];

  const datasetChartData = temporalData?.dataset_popularity?.slice(0, 7).map((d) => {
    const totalMentions = Object.values(d.counts || {}).reduce((a, b) => a + b, 0);
    return { name: d.name, mentions: totalMentions };
  }) || [];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-6">
        <div>
          <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1 uppercase tracking-wider">
            <Compass className="h-4 w-4" /> Research Intelligence Cockpit • Active Workspace
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Workspace</h1>
          <p className="text-muted-foreground mt-1">
            Read papers, review limitations, and develop your next study.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {projects.length > 0 && (
            <select
              className="h-10 rounded-lg border border-input bg-card px-3 py-2 text-sm shadow-sm"
              value={effectiveProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          )}

          <Link to="/projects/new">
            <Button className="shadow-sm">
              <Plus className="mr-2 h-4 w-4" />
              New Project
            </Button>
          </Link>
        </div>
      </div>

      <ManuscriptStudio key={effectiveProjectId} projectId={effectiveProjectId} paperOnly />
      {/* Research progress */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Research Progress ({projects.find((p) => p.id === effectiveProjectId)?.title || "Current Workspace"})
        </h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {[
            {
              label: "Corpus Papers",
              value: summary?.papers ?? 0,
              icon: BookOpen,
              color: "text-blue-600 dark:text-blue-400",
              bgColor: "bg-blue-50 dark:bg-blue-950/40",
            },
            {
              label: "Evidence Claims",
              value: summary?.claims ?? 0,
              icon: ShieldCheck,
              color: "text-emerald-600 dark:text-emerald-400",
              bgColor: "bg-emerald-50 dark:bg-emerald-950/40",
            },
            {
              label: "Potential Gaps",
              value: summary?.research_gaps ?? 0,
              icon: FileText,
              color: "text-amber-600 dark:text-amber-400",
              bgColor: "bg-amber-50 dark:bg-amber-950/40",
            },
            {
              label: "Hypotheses",
              value: summary?.hypotheses ?? 0,
              icon: Lightbulb,
              color: "text-purple-600 dark:text-purple-400",
              bgColor: "bg-purple-50 dark:bg-purple-950/40",
            },
            {
              label: "Experiments",
              value: summary?.experiments ?? 0,
              icon: FlaskConical,
              color: "text-rose-600 dark:text-rose-400",
              bgColor: "bg-rose-50 dark:bg-rose-950/40",
            },
            {
              label: "Reports",
              value: summary?.reports ?? 0,
              icon: Layers,
              color: "text-indigo-600 dark:text-indigo-400",
              bgColor: "bg-indigo-50 dark:bg-indigo-950/40",
            },
          ].map(({ label, value, icon: Icon, color, bgColor }) => (
            <Card key={label} className="shadow-sm border">
              <CardContent className="flex flex-col justify-between p-4 h-full">
                <div className={`p-2 w-fit rounded-lg ${bgColor} mb-3`}>
                  <Icon className={`h-5 w-5 ${color}`} />
                </div>
                <div>
                  <p className="text-2xl font-bold tracking-tight">{value}</p>
                  <p className="text-xs text-muted-foreground font-medium mt-0.5">{label}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Spec Module S: Research Landscape Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Papers by Publication Year */}
        <Card className="shadow-sm border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" /> Literature Publication Timeline
            </CardTitle>
            <CardDescription className="text-xs">
              Chronological distribution of ingested academic papers across conference & arXiv releases.
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64 pt-4">
            {timelineChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={timelineChartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="year" fontSize={11} />
                  <YAxis allowDecimals={false} fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="papers" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Papers" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                No publication timeline data available for this project.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Model Popularity & Benchmarks */}
        <Card className="shadow-sm border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" /> Model & Dataset Entity Prevalence
            </CardTitle>
            <CardDescription className="text-xs">
              Model and dataset mentions extracted from this project corpus.
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64 pt-4">
            {modelChartData.length > 0 || datasetChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={modelChartData.length > 0 ? modelChartData : datasetChartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis type="number" allowDecimals={false} fontSize={11} />
                  <YAxis dataKey="name" type="category" width={110} fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="mentions" fill="#8b5cf6" radius={[0, 4, 4, 0]} name="Mentions" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                No model or dataset distribution available yet.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects Workspace Directory */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold tracking-tight">Projects</h2>
          <Link to="/projects" className="text-xs text-primary hover:underline flex items-center gap-1 font-medium">
            View all ({projectsData?.total ?? 0}) <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {projectsLoading ? (
          <p className="text-muted-foreground text-sm">Loading research workspaces...</p>
        ) : projects.length === 0 ? (
          <div className="text-center py-12 border rounded-lg bg-muted/20">
            <BookOpen className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
            <p className="text-sm font-medium">No research projects created yet.</p>
            <p className="text-xs text-muted-foreground mt-1">Start by formulating your primary NLP research question.</p>
            <Link to="/projects/new">
              <Button size="sm" className="mt-4">Create your first project</Button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.slice(0, 4).map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`}>
                <Card className="hover:border-primary/50 transition-all cursor-pointer h-full flex flex-col justify-between shadow-sm">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between gap-2">
                      <Badge className={STATUS_COLORS[project.status]}>{project.status}</Badge>
                      <span className="text-[11px] text-muted-foreground">Updated {formatDate(project.updated_at)}</span>
                    </div>
                    <CardTitle className="text-base font-semibold leading-snug mt-2">
                      {project.title}
                    </CardTitle>
                    {project.description && (
                      <CardDescription className="text-xs line-clamp-2 mt-1">
                        {project.description}
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="flex items-center justify-between text-xs text-muted-foreground border-t pt-3 mt-2">
                      <span>Status: {project.status.toUpperCase()}</span>
                      <span className="text-primary font-medium flex items-center gap-1">
                        Open Project <ArrowRight className="h-3 w-3" />
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
