import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getRoleDetail, explainRole } from '../api';
import './RoleDetail.css';

function RoleDetail() {
  const { roleName } = useParams();
  const [roleData, setRoleData] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRoleData();
  }, [roleName]);

  const loadRoleData = async () => {
    try {
      setLoading(true);
      const decodedRoleName = decodeURIComponent(roleName ?? '');
      const [roleRes, explainRes] = await Promise.all([
        getRoleDetail(decodedRoleName),
        explainRole(decodedRoleName)
      ]);
      setRoleData(roleRes.data);
      setExplanation(explainRes.data);
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err.message ||
        'Failed to load role details';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading role details...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!roleData) return <div className="loading">Role not found</div>;

  const permissions = roleData.permissions ?? [];
  const escalationRisks = roleData.escalation_risks ?? [];
  const wildcardRisks = roleData.wildcard_risks ?? [];
  const complianceGaps = roleData.compliance_gaps ?? [];

  return (
    <div className="role-detail">
      <Link to="/" className="back-link">← Back to Dashboard</Link>
      <h1>Role Details: {roleData.role}</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <div className={`stat-value risk-${roleData.risk_level ?? 'low'}`}>
            {roleData.risk_score}/100
          </div>
          <div className="stat-label">Risk Score</div>
        </div>
        <div className="stat-card">
          <div className={`stat-value risk-${roleData.risk_level ?? 'low'}`}>
            {(roleData.risk_level ?? 'low').toUpperCase()}
          </div>
          <div className="stat-label">Risk Level</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{roleData.cloud || 'N/A'}</div>
          <div className="stat-label">Cloud Provider</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{permissions.length}</div>
          <div className="stat-label">Total Permissions</div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">LLM Insights</h2>
        <div className={`llm-badge ${roleData.llm_available ? 'llm-available' : 'llm-fallback'}`}>
          {roleData.llm_available ? 'LLM Powered' : 'Rule-Based'}
        </div>
        <p className="explanation-text">{explanation?.explanation || roleData.llm_explanation || 'No explanation available.'}</p>
      </div>

      {escalationRisks.length > 0 && (
        <div className="card">
          <h2 className="card-title">Escalation Risks</h2>
          <ul className="risk-list">
            {escalationRisks.map((risk, idx) => (
              <li key={idx} className="risk-item">
                <strong>Risky Permissions:</strong> {(risk.risky_permissions ?? []).join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}

      {wildcardRisks.length > 0 && (
        <div className="card">
          <h2 className="card-title">Wildcard Permissions</h2>
          <ul className="risk-list">
            {wildcardRisks.map((risk, idx) => (
              <li key={idx} className="risk-item">
                <strong>Wildcards:</strong> {(risk.wildcard_permissions ?? []).join(', ')}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card">
        <h2 className="card-title">Permissions ({permissions.length})</h2>
        <div className="permissions-grid">
          {permissions.slice(0, 50).map((perm, idx) => (
            <div key={idx} className="permission-tag">{typeof perm === 'string' ? perm : JSON.stringify(perm)}</div>
          ))}
          {permissions.length > 50 && (
            <div className="permission-tag">+{permissions.length - 50} more</div>
          )}
        </div>
      </div>

      {complianceGaps.length > 0 && (
        <div className="card">
          <h2 className="card-title">Compliance Gaps</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Standard</th>
                <th>Control</th>
                <th>Finding</th>
              </tr>
            </thead>
            <tbody>
              {complianceGaps.map((gap, idx) => (
                <tr key={idx}>
                  <td>{gap.standard}</td>
                  <td>{gap.control}</td>
                  <td>{gap.finding}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default RoleDetail;
