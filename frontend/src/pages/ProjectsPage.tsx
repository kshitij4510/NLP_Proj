import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useProjects, useCreateProject, useDeleteProject } from "@/hooks/useProjects";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Loader2, Trash2, ArrowRight } from "lucide-react";
import { formatDate, STATUS_COLORS } from "@/lib/utils";

export default function ProjectsPage() {
  const { data, isLoading } = useProjects({ page_size: 50 });
  const createProject = useCreateProject();
  const deleteProject = useDeleteProject();
  const [showForm, setShowForm] = useState(useLocation().pathname === "/projects/new");
  const [title, setTitle] = useState("");
  const [question, setQuestion] = useState("");

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createProject.mutate(
      { title, research_question: question ? { question } : undefined },
      { onSuccess: () => { setShowForm(false); setTitle(""); setQuestion(""); } }
    );
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Projects</h1>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="mr-2 h-4 w-4" />
          New Project
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardContent className="p-4">
            <form onSubmit={handleCreate} className="space-y-3">
              <Input
                placeholder="Project title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
              <Input
                placeholder="Primary research question (optional)"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />
              <div className="flex gap-2">
                <Button type="submit" disabled={createProject.isPending}>
                  {createProject.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="space-y-3">
          {data?.items.map((project) => (
            <Card key={project.id} className="hover:shadow-sm transition-shadow">
              <CardContent className="flex items-center justify-between p-4">
                <Link to={`/projects/${project.id}`} className="flex-1 min-w-0">
                  <p className="font-medium truncate">{project.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {project.description ?? "No description"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">{formatDate(project.updated_at)}</p>
                </Link>
                <div className="flex items-center gap-2 ml-4">
                  <Badge className={STATUS_COLORS[project.status]}>{project.status}</Badge>
                  <Link to={`/projects/${project.id}`}>
                    <Button variant="ghost" size="icon">
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive hover:text-destructive"
                    onClick={() => deleteProject.mutate(project.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
          {data?.items.length === 0 && (
            <div className="text-center py-16 text-muted-foreground">
              No projects yet. Create one to start your research.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
