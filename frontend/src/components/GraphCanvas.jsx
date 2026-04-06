import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";

cytoscape.use(dagre);

export default function GraphCanvas({ elements, onNodeClick }) {
  return (
    <div className="card h-[70vh]">
      <CytoscapeComponent
        elements={elements}
        style={{ width: "100%", height: "100%" }}
        layout={{ name: "dagre" }}
        stylesheet={[
          { selector: "node", style: { label: "data(label)", color: "#fff", "background-color": "#666", width: "mapData(risk, 0, 100, 20, 60)", height: "mapData(risk, 0, 100, 20, 60)" } },
          { selector: 'node[cloud = "aws"]', style: { "background-color": "#f59e0b" } },
          { selector: 'node[cloud = "azure"]', style: { "background-color": "#3b82f6" } },
          { selector: 'node[cloud = "gcp"]', style: { "background-color": "#22c55e" } },
          { selector: "edge", style: { label: "data(label)", "line-color": "#00d4ff", "target-arrow-shape": "triangle", "target-arrow-color": "#00d4ff", color: "#94a3b8", width: 2 } },
        ]}
        cy={(cy) => cy.on("tap", "node", (e) => onNodeClick?.(e.target.data()))}
      />
    </div>
  );
}

