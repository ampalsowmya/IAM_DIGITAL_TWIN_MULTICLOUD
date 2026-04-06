import { useEffect, useMemo, useState } from "react";
import GraphCanvas from "../components/GraphCanvas";
import { apiClient } from "../api/client";

export default function GraphExplorer() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [selected, setSelected] = useState(null);
  useEffect(() => { apiClient.graph().then((r) => setGraph(r.data)); }, []);
  const elements = useMemo(() => [
    ...graph.nodes.map((n) => ({ data: { id: String(n.nid), label: n.props?.name || n.nid, cloud: n.props?.cloud || "aws", risk: n.props?.risk_score || 10, ...n.props } })),
    ...graph.edges.map((e, i) => ({ data: { id: `e${i}`, source: String(e.source), target: String(e.target), label: e.label } })),
  ], [graph]);
  return <div className="grid md:grid-cols-[1fr_320px] gap-4"><GraphCanvas elements={elements} onNodeClick={setSelected} /><div className="card"><h3 className="font-bold mb-2">Node Details</h3><pre className="text-xs whitespace-pre-wrap">{JSON.stringify(selected, null, 2)}</pre></div></div>;
}

