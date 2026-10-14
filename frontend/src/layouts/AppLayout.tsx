import { Outlet, NavLink, useNavigate } from "react-router-dom";
import {
  BookOpen, FlaskConical, LayoutDashboard, LogOut,
  FileText, Network, Search, Lightbulb, Compass,
  ShieldCheck, AlertCircle, Sparkles, Settings, FolderKanban
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useLogout } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const mainNav = [
  { to: "/about", icon: BookOpen, label: "About & bibliography" },
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/planner", icon: Compass, label: "Research Planner" },
  { to: "/literature", icon: BookOpen, label: "Literature Explorer" },
  { to: "/evidence", icon: ShieldCheck, label: "Evidence Provenance" },
  { to: "/graph", icon: Network, label: "Knowledge Graph" },
  { to: "/gaps", icon: AlertCircle, label: "Research Gaps" },
  { to: "/hypotheses", icon: Sparkles, label: "Hypothesis Lab" },
  { to: "/experiments", icon: FlaskConical, label: "Experiments & Runs" },
  { to: "/reports", icon: FileText, label: "IEEE Papers & Reports" },
  { to: "/search", icon: Search, label: "Hybrid Search" },
  { to: "/projects", icon: FolderKanban, label: "All Projects" },
  { to: "/settings", icon: Settings, label: "Runtime Diagnostics" },
];

export function AppLayout() {
  const logout = useLogout();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col border-r bg-card shrink-0">
        {/* Brand */}
        <div className="flex h-16 items-center px-4 border-b gap-2.5">
          <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
            <Lightbulb className="h-5 w-5" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight text-foreground block leading-tight">
              ResearchMind
            </span>
            <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">
              Research notebook
            </span>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 space-y-1 p-3 overflow-y-auto">
          {mainNav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-xs font-semibold"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer / Sign out */}
        <div className="p-3 border-t bg-muted/20">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-xs text-muted-foreground hover:text-destructive"
            onClick={logout}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
