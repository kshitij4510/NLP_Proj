import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { knowledgeApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Loader2, Network, BarChart3, ShieldCheck, Share2, Layers, Filter } from "lucide-react";
import { useProjects } from "@/hooks/useProjects";
import { InteractiveGraph, type GraphNode, type GraphLink } from "@/components/common/InteractiveGraph";

const ENTITY_COLORS: Record<string, string> = {
  MODEL: "#3b82f6",
  DATASET: "#10b981",
  TASK: "#f59e0b",
  METRIC: "#ef4444",
  METHOD: "#8b5cf6",
  BENCHMARK: "#ec4899",
  ORGANIZATION: "#64748b",
};

export default function KnowledgeGraphPage() {
  const { data: projects } = useProjects({ page_size: 50 });
  const [selectedProject, setSelectedProject] = useState("");
  const [activeTab, setActiveTab] = useState<"graph" | "analytics">("graph");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const effectiveProjectId = selectedProject || (projects?.items[0]?.id ?? "");

  const { data: distribution, isLoading: distLoading } = useQuery({
    queryKey: ["knowledge", effectiveProjectId, "distribution"],
    queryFn: () => knowledgeApi.getEntityDistribution(effectiveProjectId),
    enabled: !!effectiveProjectId,
  });

  const { data: entities, isLoading: entLoading } = useQuery({
    queryKey: ["knowledge", effectiveProjectId, "entities"],
    queryFn: () => knowledgeApi.listEntities(effectiveProjectId, { page_size: 150 } as any),
    enabled: !!effectiveProjectId,
  });

  const { data: relationships, isLoading: relLoading } = useQuery({
    queryKey: ["knowledge", effectiveProjectId, "relationships"],
    queryFn: () => knowledgeApi.listRelationships(effectiveProjectId, { page_size: 100 } as any),
    enabled: !!effectiveProjectId,
  });

  const { data: claims } = useQuery({
    queryKey: ["knowledge", effectiveProjectId, "claims"],
    queryFn: () => knowledgeApi.listClaims(effectiveProjectId),
    enabled: !!effectiveProjectId,
  });

  // Prepare D3 Graph Nodes & Links
  const { graphNodes, graphLinks } = useMemo(() => {
    if (!entities?.items) return { graphNodes: [], graphLinks: [] };

    const nodeMap = new Map<string, GraphNode>();
    entities.items.forEach((e: any) => {
      nodeMap.set(e.name, {
        id: e.name,
        name: e.name,
        type: e.entity_type,
        paperId: e.paper_id,
        confidence: e.confidence,
      });
    });

    const links: GraphLink[] = [];
    (relationships?.items || []).forEach((r: any) => {
      if (!nodeMap.has(r.source)) {
        nodeMap.set(r.source, { id: r.source, name: r.source, type: "METHOD" });
      }
      if (!nodeMap.has(r.target)) {
        nodeMap.set(r.target, { id: r.target, name: r.target, type: "TASK" });
      }
      links.push({
        source: r.source,
        target: r.target,
        relation: r.relation_type,
      });
    });

    return {
      graphNodes: Array.from(nodeMap.values()),
      graphLinks: links,
    };
  }, [entities, relationships]);

  const distData = distribution
    ? Object.entries(distribution.distribution).map(([type, count]) => ({ type, count }))
    : [];

  const isLoading = distLoading || entLoading || relLoading;

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Network className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Scientific Knowledge Graph</h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Explore models, datasets, metrics, and empirical claims extracted with citation grounding.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm font-medium shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            value={effectiveProjectId}
            onChange={(e) => {
              setSelectedProject(e.target.value);
              setSelectedNode(null);
            }}
          >
            {projects?.items.map((p) => (
              <option key={p.id} value={p.id}>{p.title}</option>
            ))}
          </select>

          <div className="flex rounded-md border p-1 bg-muted/40">
            <Button
              variant={activeTab === "graph" ? "default" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("graph")}
              className="h-7 text-xs gap-1.5"
            >
              <Share2 className="h-3.5 w-3.5" /> Force Graph
            </Button>
            <Button
              variant={activeTab === "analytics" ? "default" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("analytics")}
              className="h-7 text-xs gap-1.5"
            >
              <BarChart3 className="h-3.5 w-3.5" /> Analytics & Claims
            </Button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : activeTab === "graph" ? (
        /* D3 Force-Directed Graph View */
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            <Card className="overflow-hidden border shadow-sm">
              <CardHeader className="py-3 px-4 border-b flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-medium">Interactive Graph Explorer</CardTitle>
                  <CardDescription className="text-xs">
                    {graphNodes.length} entities • {graphLinks.length} grounded relationships • Click & drag nodes to inspect
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {Object.entries(ENTITY_COLORS).map(([type, color]) => (
                    <div key={type} className="hidden sm:flex items-center gap-1 text-[11px] text-muted-foreground">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                      <span>{type}</span>
                    </div>
                  ))}
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <InteractiveGraph
                  nodes={graphNodes}
                  links={graphLinks}
                  onSelectNode={(n) => setSelectedNode(n)}
                />
              </CardContent>
            </Card>
          </div>

          {/* Node Inspector Drawer */}
          <div className="lg:col-span-1 space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Layers className="h-4 w-4 text-primary" />
                  Entity Inspector
                </CardTitle>
                <CardDescription className="text-xs">
                  {selectedNode ? "Inspecting selected entity" : "Click any node in the graph to view details"}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {selectedNode ? (
                  <div className="space-y-3">
                    <div>
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Entity Name</span>
                      <h3 className="text-base font-bold text-foreground mt-0.5">{selectedNode.name}</h3>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge
                        style={{
                          backgroundColor: `${ENTITY_COLORS[selectedNode.type] || "#3b82f6"}20`,
                          color: ENTITY_COLORS[selectedNode.type] || "#3b82f6",
                          borderColor: ENTITY_COLORS[selectedNode.type] || "#3b82f6",
                        }}
                        className="text-xs font-semibold"
                      >
                        {selectedNode.type}
                      </Badge>
                      {selectedNode.confidence && (
                        <span className="text-xs text-muted-foreground">
                          {(selectedNode.confidence * 100).toFixed(0)}% confidence
                        </span>
                      )}
                    </div>

                    {selectedNode.paperId && (
                      <div className="pt-2 border-t">
                        <span className="text-[11px] text-muted-foreground uppercase font-semibold">Source Paper ID</span>
                        <p className="text-xs font-mono text-muted-foreground mt-0.5 break-all">
                          {selectedNode.paperId}
                        </p>
                      </div>
                    )}

                    <div className="pt-2 border-t">
                      <span className="text-[11px] text-muted-foreground uppercase font-semibold">Connected Relations</span>
                      <div className="mt-1.5 space-y-1.5 max-h-48 overflow-y-auto">
                        {graphLinks
                          .filter((l) => {
                            const src = typeof l.source === "object" ? (l.source as any).id : l.source;
                            const tgt = typeof l.target === "object" ? (l.target as any).id : l.target;
                            return src === selectedNode.id || tgt === selectedNode.id;
                          })
                          .map((l, idx) => {
                            const src = typeof l.source === "object" ? (l.source as any).id : l.source;
                            const tgt = typeof l.target === "object" ? (l.target as any).id : l.target;
                            return (
                              <div key={idx} className="p-1.5 rounded bg-muted/30 border text-[11px] space-y-0.5">
                                <span className="font-semibold text-primary">{l.relation}</span>
                                <div className="text-muted-foreground truncate">
                                  {src === selectedNode.id ? `→ ${tgt}` : `← ${src}`}
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-12 text-center text-xs text-muted-foreground">
                    No node selected. Click on a circle in the force graph.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        /* Analytics & Claims View */
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Entity distribution chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Entity Type Distribution</CardTitle>
              <CardDescription className="text-xs">
                NLP entity counts by structural category across all ingested papers.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {distData.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={distData}>
                    <XAxis dataKey="type" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {distData.map((entry, i) => (
                        <Cell key={i} fill={ENTITY_COLORS[entry.type] ?? "#6b7280"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-muted-foreground py-8 text-center">No entities extracted yet.</p>
              )}
            </CardContent>
          </Card>

          {/* Claims verification summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center justify-between">
                <span>Verified Empirical Claims</span>
                <Badge variant="outline">{claims?.total ?? 0} total</Badge>
              </CardTitle>
              <CardDescription className="text-xs">
                Claims extracted from research papers with exact status grounding.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2.5 max-h-60 overflow-y-auto">
                {claims?.items.map((claim) => (
                  <div key={claim.id} className="flex items-start gap-2 py-1.5 border-b last:border-0">
                    <Badge
                      variant={
                        claim.verification_status === "SUPPORTED"
                          ? "success"
                          : claim.verification_status === "CONTRADICTED"
                          ? "destructive"
                          : "outline"
                      }
                      className="shrink-0 text-[10px]"
                    >
                      {claim.verification_status}
                    </Badge>
                    <p className="text-xs text-muted-foreground line-clamp-2">{claim.claim_text}</p>
                  </div>
                ))}
                {!claims?.items.length && (
                  <p className="text-sm text-muted-foreground py-4 text-center">No claims yet.</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Relationships Table */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-base flex items-center justify-between">
                <span>Extracted Relationships</span>
                <Badge variant="outline">{relationships?.total ?? 0} total</Badge>
              </CardTitle>
              <CardDescription className="text-xs">
                Predicate relationships linking models, benchmarks, metrics, and tasks.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {relationships?.items.map((rel: any) => (
                  <div key={rel.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 py-2 border-b last:border-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-foreground">{rel.source}</span>
                      <Badge variant="secondary" className="text-[10px]">{rel.relation_type}</Badge>
                      <span className="font-semibold text-xs text-foreground">{rel.target}</span>
                    </div>
                    {rel.evidence_snippet && (
                      <p className="text-xs text-muted-foreground italic line-clamp-1 max-w-md">
                        "{rel.evidence_snippet}"
                      </p>
                    )}
                  </div>
                ))}
                {!relationships?.items.length && (
                  <p className="text-sm text-muted-foreground py-4 text-center">No relationships yet.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
