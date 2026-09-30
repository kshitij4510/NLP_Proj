import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

export interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: string;
  paperId?: string;
  context?: string;
  confidence?: number;
}

export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
  relation: string;
}

interface InteractiveGraphProps {
  nodes: GraphNode[];
  links: GraphLink[];
  onSelectNode?: (node: GraphNode | null) => void;
}

const TYPE_COLORS: Record<string, string> = {
  MODEL: "#3b82f6",       // Blue
  DATASET: "#10b981",     // Emerald
  TASK: "#f59e0b",        // Amber
  METRIC: "#ef4444",       // Rose
  METHOD: "#8b5cf6",      // Purple
  BENCHMARK: "#ec4899",   // Pink
  ORGANIZATION: "#64748b",// Slate
  CLAIM: "#06b6d4",       // Cyan
};

export function InteractiveGraph({ nodes, links, onSelectNode }: InteractiveGraphProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const width = svgRef.current.clientWidth || 800;
    const height = 540;

    // Clone data so D3 simulation doesn't mutate props directly
    const simNodes: GraphNode[] = nodes.map((d) => ({ ...d }));
    const simLinks: GraphLink[] = links.map((d) => ({ ...d }));

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Defs for arrowheads
    const defs = svg.append("defs");
    defs.append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 22)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#94a3b8");

    const container = svg.append("g").attr("class", "graph-container");

    // Zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 4])
      .on("zoom", (event) => {
        container.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Force simulation
    const simulation = d3.forceSimulation<GraphNode>(simNodes)
      .force(
        "link",
        d3.forceLink<GraphNode, GraphLink>(simLinks)
          .id((d) => d.id)
          .distance(90)
      )
      .force("charge", d3.forceManyBody().strength(-240))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius(28));

    // Links
    const link = container.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(simLinks)
      .enter()
      .append("line")
      .attr("stroke", "#cbd5e1")
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.7)
      .attr("marker-end", "url(#arrow)");

    // Link labels
    const linkLabels = container.append("g")
      .attr("class", "link-labels")
      .selectAll("text")
      .data(simLinks)
      .enter()
      .append("text")
      .attr("font-size", "9px")
      .attr("fill", "#64748b")
      .attr("text-anchor", "middle")
      .text((d) => d.relation);

    // Nodes
    const node = container.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(simNodes)
      .enter()
      .append("g")
      .attr("cursor", "pointer")
      .call(
        d3.drag<SVGGElement, GraphNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Node circles
    node.append("circle")
      .attr("r", 14)
      .attr("fill", (d) => TYPE_COLORS[d.type] || "#64748b")
      .attr("stroke", "#ffffff")
      .attr("stroke-width", 2)
      .attr("class", "transition-transform hover:scale-125");

    // Node labels
    node.append("text")
      .attr("dx", 18)
      .attr("dy", 4)
      .attr("font-size", "11px")
      .attr("font-weight", "500")
      .attr("fill", "currentColor")
      .text((d) => d.name);

    // Click handler
    node.on("click", (event, d) => {
      event.stopPropagation();
      setSelectedNode(d);
      if (onSelectNode) onSelectNode(d);
    });

    svg.on("click", () => {
      setSelectedNode(null);
      if (onSelectNode) onSelectNode(null);
    });

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      linkLabels
        .attr("x", (d: any) => (d.source.x + d.target.x) / 2)
        .attr("y", (d: any) => (d.source.y + d.target.y) / 2 - 3);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, links]);

  return (
    <div className="relative w-full border rounded-xl bg-card/60 backdrop-blur-sm shadow-sm overflow-hidden">
      {/* Legend */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap gap-2 p-2 bg-background/90 rounded-lg border text-xs shadow-sm backdrop-blur">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1.5 font-medium">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {type}
          </span>
        ))}
      </div>

      <svg ref={svgRef} className="w-full h-[540px]" />
    </div>
  );
}
