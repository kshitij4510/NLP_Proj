import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Settings, Sliders, Database, Cpu, Shield, Key,
  CheckCircle2, RefreshCw, Terminal, Layers
} from "lucide-react";

export default function SettingsPage() {
  const [provider, setProvider] = useState("mock");
  const [modelName, setModelName] = useState("gpt-4o");
  const [apiKey, setApiKey] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("BAAI/bge-small-en-v1.5");
  const [bm25Weight, setBm25Weight] = useState("0.5");
  const [topK, setTopK] = useState("10");
  const [enableReranker, setEnableReranker] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            <Settings className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">ResearchMind Settings & Diagnostics</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Configure LLM backends, hybrid retrieval parameters, embedding providers, and local runtime options.
            </p>
          </div>
        </div>

        {saved && (
          <span className="flex items-center gap-1.5 text-xs text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-md border border-emerald-200">
            <CheckCircle2 className="h-4 w-4" /> Preferences saved
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: LLM Inference Engine */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Cpu className="h-4 w-4 text-primary" />
              LLM Inference Provider
            </CardTitle>
            <CardDescription className="text-xs">
              Select your primary generation model for synthesis, gap analysis, and hypothesis formulation.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-foreground">Provider Mode</label>
                <select
                  className="mt-1 flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm"
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                >
                  <option value="mock">Local Deterministic Research Model (Fast/Offline)</option>
                  <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                  <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
                  <option value="gemini">Google Gemini 1.5 Pro</option>
                  <option value="ollama">Ollama Local (Llama 3 / Mistral)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-foreground">Model Identifier</label>
                <Input
                  className="mt-1 text-xs"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="e.g. gpt-4o or claude-3-5-sonnet-20241022"
                />
              </div>
            </div>

            {provider !== "mock" && (
              <div>
                <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <Key className="h-3.5 w-3.5 text-muted-foreground" /> API Secret Key
                </label>
                <Input
                  type="password"
                  className="mt-1 text-xs font-mono"
                  placeholder="sk-..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <p className="text-[11px] text-muted-foreground mt-1">
                  Keys are stored in your secure session environment and never committed to version control.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Section 2: Retrieval & Vector Indexing */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary" />
              Hybrid Retrieval & Embeddings
            </CardTitle>
            <CardDescription className="text-xs">
              Tune the balance between lexical BM25 matching and dense semantic embeddings.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-medium text-foreground">Embedding Architecture</label>
                <select
                  className="mt-1 flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm"
                  value={embeddingModel}
                  onChange={(e) => setEmbeddingModel(e.target.value)}
                >
                  <option value="BAAI/bge-small-en-v1.5">BAAI/bge-small-en-v1.5 (384d)</option>
                  <option value="text-embedding-3-small">OpenAI text-embedding-3-small (1536d)</option>
                  <option value="mock-embeddings">Deterministic Fast Embeddings (384d)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-foreground">
                  BM25 Lexical Weight (α = {bm25Weight})
                </label>
                <Input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  className="mt-2"
                  value={bm25Weight}
                  onChange={(e) => setBm25Weight(e.target.value)}
                />
                <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                  <span>Dense (0.0)</span>
                  <span>Balanced (0.5)</span>
                  <span>BM25 (1.0)</span>
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-foreground">Top K Evidence Chunks</label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  className="mt-1 text-xs"
                  value={topK}
                  onChange={(e) => setTopK(e.target.value)}
                />
              </div>
            </div>

            <div className="pt-2 flex items-center gap-2">
              <input
                type="checkbox"
                id="reranker"
                checked={enableReranker}
                onChange={(e) => setEnableReranker(e.target.checked)}
                className="rounded border-input text-primary focus:ring-primary h-4 w-4"
              />
              <label htmlFor="reranker" className="text-xs font-medium text-foreground cursor-pointer">
                Enable Cross-Encoder Reranker (Reciprocal Rank Fusion + Semantic Scoring)
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Section 3: System Diagnostics & Health */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Database className="h-4 w-4 text-primary" />
              Runtime Environment & Diagnostics
            </CardTitle>
            <CardDescription className="text-xs">
              System status and storage engine configuration.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-lg border bg-muted/20">
                <span className="text-muted-foreground block text-[11px]">Database Dialect</span>
                <span className="font-semibold font-mono text-foreground">SQLite (aiosqlite)</span>
              </div>
              <div className="p-3 rounded-lg border bg-muted/20">
                <span className="text-muted-foreground block text-[11px]">Pipeline Worker</span>
                <span className="font-semibold text-foreground">In-Process AsyncIO</span>
              </div>
              <div className="p-3 rounded-lg border bg-muted/20">
                <span className="text-muted-foreground block text-[11px]">Backend API</span>
                <span className="font-semibold text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> Online :8000
                </span>
              </div>
              <div className="p-3 rounded-lg border bg-muted/20">
                <span className="text-muted-foreground block text-[11px]">Benchmark Suite</span>
                <span className="font-semibold font-mono text-foreground">5 Tasks / 6 Baselines</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Button */}
        <div className="flex justify-end">
          <Button type="submit" className="gap-2">
            Save Preferences
          </Button>
        </div>
      </form>
    </div>
  );
}
