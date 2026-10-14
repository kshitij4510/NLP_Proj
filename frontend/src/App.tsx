import { Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { useAuthStore } from "@/lib/store";
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import ProjectsPage from "@/pages/ProjectsPage";
import ProjectDetailPage from "@/pages/ProjectDetailPage";
import PlannerPage from "@/pages/PlannerPage";
import LiteraturePage from "@/pages/LiteraturePage";
import PaperViewerPage from "@/pages/PaperViewerPage";
import EvidenceExplorerPage from "@/pages/EvidenceExplorerPage";
import KnowledgeGraphPage from "@/pages/KnowledgeGraphPage";
import GapsPage from "@/pages/GapsPage";
import HypothesesPage from "@/pages/HypothesesPage";
import ExperimentsPage from "@/pages/ExperimentsPage";
import ReportsPage from "@/pages/ReportsPage";
import SearchPage from "@/pages/SearchPage";
import AboutPage from "@/pages/AboutPage";
import SettingsPage from "@/pages/SettingsPage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      {/* Public Landing & Auth */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<LoginPage />} />

      {/* Authenticated Workspace App */}
      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/new" element={<ProjectsPage />} />
        <Route path="/projects/:id" element={<ProjectDetailPage />} />
        <Route path="/projects/:projectId/papers/:paperId" element={<PaperViewerPage />} />
        <Route path="/planner" element={<PlannerPage />} />
        <Route path="/literature" element={<LiteraturePage />} />
        <Route path="/evidence" element={<EvidenceExplorerPage />} />
        <Route path="/graph" element={<KnowledgeGraphPage />} />
        <Route path="/gaps" element={<GapsPage />} />
        <Route path="/hypotheses" element={<HypothesesPage />} />
        <Route path="/experiments" element={<ExperimentsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/settings" element={<SettingsPage />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}
