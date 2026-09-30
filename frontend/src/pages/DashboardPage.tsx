import { useProjects } from "@/hooks/useProjects";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, BookOpen, FlaskConical, FileText, Lightbulb } from "lucide-react";
import { formatDate, STATUS_COLORS } from "@/lib/utils";

export default function DashboardPage() {
  const { data, isLoading } = useProjects({ page_size: 5 });

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Your research workspace</p>
        </div>
        <Link to="/projects/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        </Link>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "Projects", value: data?.total ?? 0, icon: BookOpen, color: "text-blue-600" },
          { label: "Papers", value: "–", icon: FileText, color: "text-purple-600" },
          { label: "Hypotheses", value: "–", icon: Lightbulb, color: "text-amber-600" },
          { label: "Experiments", value: "–", icon: FlaskConical, color: "text-green-600" },
        ].map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="flex items-center gap-4 p-6">
              <Icon className={`h-8 w-8 ${color}`} />
              <div>
                <p className="text-2xl font-bold">{value}</p>
                <p className="text-sm text-muted-foreground">{label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent projects */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Recent Projects</h2>
        {isLoading ? (
          <p className="text-muted-foreground">Loading...</p>
        ) : data?.items.length === 0 ? (
          <div className="text-center py-12 border rounded-lg bg-muted/30">
            <BookOpen className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
            <p className="text-muted-foreground">No projects yet.</p>
            <Link to="/projects/new">
              <Button variant="outline" className="mt-3">Create your first project</Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {data?.items.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="flex items-center justify-between p-4">
                    <div>
                      <p className="font-medium">{project.title}</p>
                      <p className="text-sm text-muted-foreground">{formatDate(project.updated_at)}</p>
                    </div>
                    <Badge className={STATUS_COLORS[project.status]}>{project.status}</Badge>
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
