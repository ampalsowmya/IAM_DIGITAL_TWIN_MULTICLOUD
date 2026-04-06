import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function RiskHeatmap({ data }) {
  return (
    <div className="card h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="range" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip />
          <Bar dataKey="count" fill="#00d4ff" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getRoles } from '../api';
import './RiskHeatmap.css';

function RiskHeatmap() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await getRoles();
      const rolesList = res.data?.roles ?? [];
      setRoles(Array.isArray(rolesList) ? rolesList.slice(0, 20) : []);
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err.message ||
        'Failed to load risk heatmap data';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading heatmap...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  const chartData = roles.map(role => {
    const name = role.role ?? role.name ?? 'Unknown';
    return {
      name: name.length > 20 ? name.substring(0, 20) + '...' : name,
      fullName: name,
      riskScore: role.risk_score ?? 0,
      riskLevel: role.risk_level ?? 'low'
    };
  });

  return (
    <div className="risk-heatmap">
      <h1>Risk Heatmap</h1>
      <div className="card">
        <h2 className="card-title">Role Risk Scores</h2>
        <ResponsiveContainer width="100%" height={600}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={-45}
              textAnchor="end"
              height={100}
            />
            <YAxis />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'riskScore') return [`${value}/100`, 'Risk Score'];
                return [value, name];
              }}
              labelFormatter={(label) => {
                const item = chartData.find(d => d.name === label);
                return item ? item.fullName : label;
              }}
            />
            <Legend />
            <Bar 
              dataKey="riskScore" 
              fill="#1e3a8a"
              name="Risk Score"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default RiskHeatmap;
