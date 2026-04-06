import React, { useState, useEffect } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { getGraph } from '../api';
import './GraphView.css';

cytoscape.use(dagre);

function GraphView() {
  const [graphData, setGraphData] = useState({ elements: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadGraph();
  }, []);

  const loadGraph = async () => {
    try {
      setLoading(true);
      const res = await getGraph(null, 50);
      const nodes = res.data?.nodes ?? [];
      const edges = res.data?.edges ?? [];
      const elements = [
        ...(Array.isArray(nodes) ? nodes : []).map(node => ({
          data: { id: node.id, label: node.label, type: node.type, cloud: node.cloud }
        })),
        ...(Array.isArray(edges) ? edges : []).map(edge => ({
          data: { source: edge.source, target: edge.target, label: edge.type }
        }))
      ];
      setGraphData({ elements });
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err.message ||
        'Failed to load graph data';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const layout = { name: 'dagre', rankDir: 'LR', spacingFactor: 1.5 };
  const styleSheet = [
    { selector: 'node[type="Role"]', style: { 'background-color': '#1e3a8a', 'label': 'data(label)', 'width': 100, 'height': 100, 'shape': 'round-rectangle', 'text-valign': 'center', 'text-halign': 'center', 'color': 'white', 'font-size': '12px' }},
    { selector: 'node[type="Policy"]', style: { 'background-color': '#3b82f6', 'label': 'data(label)', 'width': 80, 'height': 80, 'shape': 'ellipse', 'text-valign': 'center', 'text-halign': 'center', 'color': 'white', 'font-size': '11px' }},
    { selector: 'node[type="Permission"]', style: { 'background-color': '#60a5fa', 'label': 'data(label)', 'width': 60, 'height': 60, 'shape': 'triangle', 'text-valign': 'center', 'text-halign': 'center', 'color': 'white', 'font-size': '10px' }},
    { selector: 'edge', style: { 'width': 2, 'line-color': '#9ca3af', 'target-arrow-color': '#9ca3af', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'label': 'data(label)', 'font-size': '10px' }}
  ];

  if (loading) return <div className="loading">Loading graph...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="graph-view">
      <h1>Graph View</h1>
      <div className="card">
        <h2 className="card-title">IAM Graph Visualization</h2>
        <div className="graph-container">
          {graphData.elements.length > 0 ? (
            <CytoscapeComponent
              elements={graphData.elements}
              style={{ width: '100%', height: '600px' }}
              layout={layout}
              stylesheet={styleSheet}
            />
          ) : (
            <div className="loading">No graph data available</div>
          )}
        </div>
        <div className="graph-legend">
          <div className="legend-item"><div className="legend-color" style={{ backgroundColor: '#1e3a8a' }}></div><span>Role</span></div>
          <div className="legend-item"><div className="legend-color" style={{ backgroundColor: '#3b82f6' }}></div><span>Policy</span></div>
          <div className="legend-item"><div className="legend-color" style={{ backgroundColor: '#60a5fa' }}></div><span>Permission</span></div>
        </div>
      </div>
    </div>
  );
}

export default GraphView;
