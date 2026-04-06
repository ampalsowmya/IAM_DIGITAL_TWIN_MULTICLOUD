import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSummary, getRoles } from '../api';
import './Dashboard.css';

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [summaryRes, rolesRes] = await Promise.all([
        getSummary(),
        getRoles()
      ]);
      setSummary(summaryRes.data);
      const rolesList = rolesRes.data?.roles ?? [];
      setRoles(Array.isArray(rolesList) ? rolesList.slice(0, 10) : []);
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err.message ||
        'Failed to load dashboard data';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!summary) return <div className="loading">No data available</div>;

  const riskSummary = summary.risk_summary ?? { high: 0, medium: 0, low: 0 };
  const escalationRisks = summary.escalation_risks ?? { direct: 0, wildcard: 0 };
  const compliance = summary.compliance ?? { iso27001: 0, nist80053: 0 };

  return (
    <div className="dashboard">
      <h1>Overview Dashboard</h1>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{summary.total_roles ?? 0}</div>
          <div className="stat-label">Total Roles</div>
        </div>
        <div className="stat-card">
          <div className="stat-value risk-high">{riskSummary.high ?? 0}</div>
          <div className="stat-label">High Risk</div>
        </div>
        <div className="stat-card">
          <div className="stat-value risk-medium">{riskSummary.medium ?? 0}</div>
          <div className="stat-label">Medium Risk</div>
        </div>
        <div className="stat-card">
          <div className="stat-value risk-low">{riskSummary.low ?? 0}</div>
          <div className="stat-label">Low Risk</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{escalationRisks.direct ?? 0}</div>
          <div className="stat-label">Escalation Risks</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{(compliance.iso27001 ?? 0).toFixed(1)}%</div>
          <div className="stat-label">ISO 27001 Compliance</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{(compliance.nist80053 ?? 0).toFixed(1)}%</div>
          <div className="stat-label">NIST 800-53 Compliance</div>
        </div>
      </div>
      <div className="card">
        <h2 className="card-title">Top Risky Roles</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Role Name</th>
              <th>Cloud</th>
              <th>Risk Score</th>
              <th>Risk Level</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((role) => (
              <tr key={role.role ?? role.name ?? Math.random()}>
                <td>{role.role ?? role.name ?? 'Unknown'}</td>
                <td>{role.cloud || 'N/A'}</td>
                <td>
                  <span className={`risk-${role.risk_level ?? 'low'}`}>
                    {role.risk_score ?? 0}/100
                  </span>
                </td>
                <td>
                  <span className={`risk-${role.risk_level ?? 'low'}`}>
                    {(role.risk_level ?? 'low').toUpperCase()}
                  </span>
                </td>
                <td>
                  <Link to={`/role/${encodeURIComponent(role.role ?? role.name ?? '')}`} className="btn btn-link">
                    View Details
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Dashboard;
