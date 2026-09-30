import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Lightbulb, Sparkles, Network, FlaskConical, FileText,
  Search, ShieldCheck, ArrowRight, GitBranch, Cpu, Database,
  Terminal, CheckCircle2, BookOpen
} from "lucide-react";

export default function LandingPage() {
  const steps = [
    { num: "01", title: "Research Planning", desc: "10-point plan with search queries, scope bounds, and inclusion criteria." },
    { num: "02", title: "Literature Discovery", desc: "ArXiv, Semantic Scholar, CrossRef automated ingestion and metadata normalization." },
    { num: "03", title: "Evidence Extraction", desc: "Verbatim chunk grounding with dense embeddings and BM25 lexical indexing." },
    { num: "04", title: "Knowledge Graph", desc: "Entity-relation extraction linking models, datasets, benchmarks, and tasks." },
    { num: "05", title: "Gap Identification", desc: "6-category taxonomy detects methodological, empirical, and theoretical voids." },
    { num: "06", title: "Hypothesis Lab", desc: "Falsifiable statements with explicit testability scores and operational variables." },
    { num: "07", title: "Experiment Protocols", desc: "Baselines, ablations, random seeds, and compute cost estimations." },
    { num: "08", title: "Report Generation", desc: "Publication-grade research paper synthesis with traceable BibTeX & APA citations." },
  ];

  const highlights = [
    {
      icon: ShieldCheck,
      title: "Evidence > Generation",
      desc: "Zero hallucinated claims. Every synthesized finding is strictly anchored to verbatim chunk provenance.",
    },
    {
      icon: Network,
      title: "Deep Knowledge Graphs",
      desc: "Interactive force-directed graph linking extracted models, metrics, datasets, and cross-paper relationships.",
    },
    {
      icon: Terminal,
      title: "CLI & API Native",
      desc: "Full terminal client, FastAPI REST endpoints, and reproducible offline evaluation benchmark suite.",
    },
    {
      icon: GitBranch,
      title: "Audit & Reproducibility",
      desc: "Track exact Git commits, hardware environments, random seeds, and confidence intervals across benchmark runs.",
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Top Navigation */}
      <header className="border-b bg-card/60 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Lightbulb className="h-5 w-5" />
            </div>
            <span className="font-bold text-lg tracking-tight">ResearchMind</span>
            <Badge variant="outline" className="text-[10px] ml-2 font-mono">
              v1.0.0
            </Badge>
          </div>

          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" size="sm" className="text-xs">
                Sign In
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button size="sm" className="gap-1.5 text-xs">
                Launch Workspace <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-24 md:py-32 px-6 border-b bg-gradient-to-b from-primary/5 via-background to-background">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <Badge variant="secondary" className="px-3 py-1 text-xs gap-1.5 inline-flex items-center">
            <Sparkles className="h-3.5 w-3.5 text-primary" /> Autonomous AI Research Scientist for NLP
          </Badge>

          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-foreground leading-[1.15]">
            From Research Question to <br className="hidden sm:inline" />
            <span className="text-primary bg-clip-text">Publication-Ready Science</span>
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto font-normal leading-relaxed">
            Investigate complex NLP questions, ingest literature, construct grounded knowledge graphs, uncover research gaps, formulate falsifiable hypotheses, and generate structured reports with verifiable citations.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
            <Link to="/dashboard">
              <Button size="lg" className="gap-2 font-medium px-6 shadow-md">
                Get Started Free <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/search">
              <Button size="lg" variant="outline" className="gap-2 px-6">
                <Search className="h-4 w-4" /> Hybrid Literature Search
              </Button>
            </Link>
          </div>

          <div className="pt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-muted-foreground font-mono">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> BM25 + Dense Hybrid RAG
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> 100% Provenance Grounding
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> BibTeX & APA Export
            </span>
          </div>
        </div>
      </section>

      {/* Core Workflow Pipeline */}
      <section className="py-20 px-6 max-w-7xl mx-auto w-full space-y-12">
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight">The 8-Stage Research Pipeline</h2>
          <p className="text-sm text-muted-foreground">
            A rigorous autonomous workflow designed around scientific methodology, not prompt shortcuts.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {steps.map((s) => (
            <Card key={s.num} className="border bg-card/50 hover:bg-card transition-all">
              <CardContent className="p-5 space-y-2">
                <span className="text-xs font-mono font-bold text-primary">{s.num}</span>
                <h3 className="font-semibold text-sm text-foreground">{s.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{s.desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Key Architectural Differentiators */}
      <section className="py-20 px-6 border-t bg-muted/20">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Engineered for Academic Rigor</h2>
            <p className="text-sm text-muted-foreground">
              Built specifically to overcome the superficiality and hallucinations of standard chatbot RAG tools.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {highlights.map((h, i) => {
              const Icon = h.icon;
              return (
                <div key={i} className="p-6 rounded-xl border bg-card space-y-3">
                  <div className="p-2.5 rounded-lg bg-primary/10 text-primary w-fit">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-base text-foreground">{h.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{h.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t py-8 px-6 bg-card text-xs text-muted-foreground">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-primary" />
            <span className="font-semibold text-foreground">ResearchMind</span>
            <span>— Autonomous AI Research Scientist for NLP</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="hover:underline">Dashboard</Link>
            <Link to="/search" className="hover:underline">Search</Link>
            <Link to="/reports" className="hover:underline">Reports</Link>
            <a href="https://github.com" target="_blank" rel="noreferrer" className="hover:underline">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
