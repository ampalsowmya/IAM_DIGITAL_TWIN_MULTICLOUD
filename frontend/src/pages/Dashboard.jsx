import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
} from "recharts";
import client from "../api/client.js";
import Header from "../components/Header.jsx";
import Sidebar from "../components/Sidebar.jsx";
import StatCard from "../components/StatCard.jsx";
import RiskDistributionChart from "../components/RiskDistributionChart.jsx";
import EscalationDonut from "../components/EscalationDonut.jsx";
import RoleRiskRegistry, {
  FILTER_ALL,
} from "../components/RoleRiskRegistry.jsx";
import HealthStatus from "../components/HealthStatus.jsx";
import PermissionHeatmap from "../components/PermissionHeatmap.jsx";

export default function Dashboard() {
  const [tab, setTab] = useState("Overview");
  const [scores, setScores] = useState([]);
  const [paths, setPaths] = useState([]);
  const [health, setHealth] = useState(null);
  const [heatmap, setHeatmap] = useState({});
  const [activity, setActivity] = useState([]);
  const [models, setModels] = useState(null);
  const [compliance, setCompliance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState(FILTER_ALL);
  const [lastScan, setLastScan] = useState("");
  const [ingestBusy, setIngestBusy] = useState(false);
  const [whatif, setWhatif] = useState({
    permissions_count: 40,
    has_admin_policy: 0,
    cross_account: 0,
    managed_policy_count: 3,
  });
  const [preview, setPreview] = useState(null);

  const load = useCallback(async () => {
    setError("");
    try {
      const [rs, ep, hz, hm, act, md, cis] = await Promise.all([
        client.get("/risk/scores"),
        client.get("/graph/escalation-paths"),
        client.get("/health"),
        client.get("/risk/heatmap"),
        client.get("/ingest/activity"),
        client.get("/risk/models"),
        client.get("/compliance/cis"),
      ]);
      setScores(rs.data || []);
      setPaths(ep.data || []);
      setHealth(hz.data);
      setHeatmap(hm.data || {});
      setActivity(act.data || []);
      setModels(md.data);
      setCompliance(cis.data || []);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadProgress = useCallback(async () => {
    try {
      const pr = await client.get("/ingest/progress");
      setLastScan(pr.data?.last_scan_utc || "");
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    load();
    loadProgress();
    const id = setInterval(() => {
      load();
      loadProgress();
    }, 10000);
    return () => clearInterval(id);
  }, [load, loadProgress]);

  useEffect(() => {
    let cancelled = false;
    async function runPreview() {
      try {
        const res = await client.post("/risk/preview", {
          permissions_count: whatif.permissions_count,
          has_admin_policy: whatif.has_admin_policy,
          cross_account: whatif.cross_account,
          managed_policy_count: whatif.managed_policy_count,
        });
        if (!cancelled) setPreview(res.data);
      } catch {
        if (!cancelled) setPreview(null);
      }
    }
    const t = setTimeout(runPreview, 200);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [whatif]);

  const stats = useMemo(() => {
    const critical = scores.filter((s) => s.level === "CRITICAL").length;
    const high = scores.filter((s) => s.level === "HIGH").length;
    const anomalies = scores.filter((s) => s.anomaly).length;
    return {
      critical,
      high,
      anomalies,
      paths: paths.length,
      total: scores.length,
    };
  }, [scores, paths]);

  const fiData = useMemo(() => {
    const imp = models?.random_forest?.feature_importance || {};
    return Object.entries(imp).map(([name, value]) => ({ name, value }));
  }, [models]);

  const anomalyRows = useMemo(
    () => scores.filter((s) => s.anomaly),
    [scores]
  );

  const scatterData = useMemo(
    () =>
      scores.map((s) => ({
        x: s.risk_score,
        y: s.if_score,
        name: s.name,
      })),
    [scores]
  );

  async function runIngest(cloud) {
    if (cloud === "all") {
      window.alert("Select AWS, Azure, or GCP to run ingestion.");
      return;
    }
    setIngestBusy(true);
    try {
      await client.post(`/ingest/${cloud}`);
      await load();
      await loadProgress();
    } catch (e) {
      window.alert(e.response?.data?.detail || e.message);
    } finally {
      setIngestBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#0a0e1a]">
      <Header activeTab={tab} onTabChange={setTab} />
      <div className="flex flex-1 min-h-0">
        <Sidebar
          scores={scores}
          lastScan={lastScan}
          onRunIngest={runIngest}
          ingestBusy={ingestBusy}
        />
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <p className="text-[11px] font-mono text-slate-500">Loading intelligence…</p>
          )}
          {error && (
            <p className="text-[11px] font-mono text-red-400" role="alert">
              {error}
            </p>
          )}

          {tab === "Overview" && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3">
                <StatCard
                  title="Critical Roles"
                  value={stats.critical}
                  subtitle="Immediate action"
                  borderClass="border-t-red-500"
                />
                <StatCard
                  title="High Risk"
                  value={stats.high}
                  subtitle="Review required"
                  borderClass="border-t-orange-500"
                />
                <StatCard
                  title="IF Anomalies"
                  value={stats.anomalies}
                  subtitle="Isolation Forest"
                  borderClass="border-t-purple-500"
                />
                <StatCard
                  title="Escalation Paths"
                  value={stats.paths}
                  subtitle="Detected"
                  borderClass="border-t-cyan-400"
                />
                <StatCard
                  title="Total Roles"
                  value={stats.total}
                  subtitle="Across connected clouds"
                  borderClass="border-t-blue-500"
                />
              </div>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <RiskDistributionChart scores={scores} />
                <EscalationDonut scores={scores} />
              </div>
              <RoleRiskRegistry
                scores={scores}
                filter={filter}
                onFilterChange={setFilter}
              />
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <PermissionHeatmap heatmap={heatmap} />
                <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] p-4 shadow-card">
                  <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase mb-4">
                    Recent Activity
                  </h3>
                  <div className="space-y-3 max-h-[260px] overflow-y-auto pr-1">
                    {activity.length === 0 && (
                      <p className="text-[10px] text-slate-600 font-mono">No events yet.</p>
                    )}
                    {activity.map((ev, i) => (
                      <div key={i} className="flex gap-3 text-[10px] font-mono border-b border-white/5 pb-2">
                        <span className="text-slate-600 shrink-0 w-36">{ev.ts}</span>
                        <span
                          className={`mt-1 h-2 w-2 rounded-full shrink-0 ${
                            ev.level === "error"
                              ? "bg-red-500"
                              : ev.level === "warn"
                                ? "bg-orange-500"
                                : ev.level === "info"
                                  ? "bg-sky-500"
                                  : "bg-emerald-500"
                          }`}
                        />
                        <div>
                          <p className="text-slate-200">{ev.title}</p>
                          <p className="text-slate-500 text-[9px] mt-0.5">{ev.detail}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}

          {tab === "ML Models" && models && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] p-4 h-[360px]">
                <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase mb-2">
                  RandomForest — Feature Importance
                </h3>
                <ResponsiveContainer width="100%" height="90%">
                  <BarChart data={fiData} layout="vertical" margin={{ left: 8, right: 16 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                    <XAxis type="number" tick={{ fill: "#64748b", fontSize: 9 }} />
                    <YAxis
                      dataKey="name"
                      type="category"
                      width={140}
                      tick={{ fill: "#64748b", fontSize: 9, fontFamily: "JetBrains Mono" }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#0f1629",
                        border: "1px solid rgba(99,179,237,0.2)",
                        fontSize: 11,
                        fontFamily: "JetBrains Mono",
                      }}
                    />
                    <Bar dataKey="value" fill="#38bdf8" radius={[0, 4, 4, 0]}>
                      {fiData.map((_, i) => (
                        <Cell key={i} fill={`hsl(${200 + i * 12}, 70%, 55%)`} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] p-4 space-y-3">
                <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase">
                  XGBoost
                </h3>
                <pre className="text-[10px] font-mono text-slate-400 overflow-auto max-h-[280px] bg-[#0a0e1a] rounded p-3 border border-white/5">
                  {JSON.stringify(models.xgboost, null, 2)}
                </pre>
                <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase pt-2">
                  Isolation Forest
                </h3>
                <pre className="text-[10px] font-mono text-slate-400 overflow-auto bg-[#0a0e1a] rounded p-3 border border-white/5">
                  {JSON.stringify(models.isolation_forest, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {tab === "Anomaly Detection" && (
            <div className="space-y-4">
              <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] overflow-hidden">
                <div className="px-4 py-3 border-b border-white/5">
                  <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase">
                    Anomalous Roles
                  </h3>
                </div>
                <table className="w-full text-[11px] font-mono">
                  <thead className="text-[9px] uppercase tracking-widest text-slate-500">
                    <tr>
                      <th className="text-left px-4 py-2">Role</th>
                      <th className="text-left px-2 py-2">IF Score</th>
                      <th className="text-left px-2 py-2">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalyRows.length === 0 && (
                      <tr>
                        <td colSpan={3} className="px-4 py-6 text-slate-600">
                          No anomalies detected.
                        </td>
                      </tr>
                    )}
                    {anomalyRows.map((r) => (
                      <tr key={r.identity_id} className="border-t border-white/5">
                        <td className="px-4 py-2 text-slate-200">{r.name}</td>
                        <td className="px-2 py-2 text-purple-400 tabular-nums">
                          {Number(r.if_score).toFixed(4)}
                        </td>
                        <td className="px-2 py-2 text-slate-300 tabular-nums">{r.risk_score}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] p-4 h-[360px]">
                <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase mb-2">
                  IF Score vs Risk Score
                </h3>
                <ResponsiveContainer width="100%" height="90%">
                  <ScatterChart margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                    <XAxis
                      type="number"
                      dataKey="x"
                      name="Risk"
                      tick={{ fill: "#64748b", fontSize: 9 }}
                      label={{ value: "risk_score", fill: "#64748b", fontSize: 9, offset: -4 }}
                    />
                    <YAxis
                      type="number"
                      dataKey="y"
                      name="IF"
                      tick={{ fill: "#64748b", fontSize: 9 }}
                      label={{ value: "if_score", fill: "#64748b", fontSize: 9, angle: -90 }}
                    />
                    <Tooltip
                      cursor={{ strokeDasharray: "3 3" }}
                      formatter={(v, name) => [v, name]}
                      labelFormatter={(_, p) => p?.[0]?.payload?.name}
                      contentStyle={{
                        background: "#0f1629",
                        border: "1px solid rgba(99,179,237,0.2)",
                        fontSize: 11,
                        fontFamily: "JetBrains Mono",
                      }}
                    />
                    <Scatter name="Roles" data={scatterData} fill="#a855f7" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {tab === "What-If Sim" && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] p-6 space-y-4">
                <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase">
                  Parameters
                </h3>
                {[
                  ["permissions_count", "Permissions count", 0, 500],
                  ["has_admin_policy", "Has AdministratorAccess (0/1)", 0, 1],
                  ["cross_account", "Cross-account trust (0/1)", 0, 1],
                  ["managed_policy_count", "Managed policies attached", 0, 30],
                ].map(([key, label, min, max]) => (
                  <label key={key} className="block">
                    <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wide">
                      {label}
                    </span>
                    <input
                      type="range"
                      min={min}
                      max={max}
                      step={key === "has_admin_policy" || key === "cross_account" ? 1 : 1}
                      value={whatif[key]}
                      onChange={(e) =>
                        setWhatif((w) => ({
                          ...w,
                          [key]: Number(e.target.value),
                        }))
                      }
                      className="w-full mt-1 accent-sky-500"
                    />
                    <span className="text-[11px] font-mono text-sky-400">{whatif[key]}</span>
                  </label>
                ))}
              </div>
              <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] p-6">
                <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase mb-4">
                  Live Preview
                </h3>
                {preview ? (
                  <div className="space-y-3 text-[12px] font-mono">
                    <p className="text-slate-300">
                      Predicted level:{" "}
                      <span className="text-amber-400">{preview.level}</span>
                    </p>
                    <p className="text-slate-300">
                      Risk score:{" "}
                      <span className="text-sky-400 tabular-nums">{preview.risk_score}</span>
                    </p>
                    <p className="text-slate-300">
                      Anomaly:{" "}
                      <span className={preview.anomaly ? "text-purple-400" : "text-emerald-400"}>
                        {preview.anomaly ? "YES" : "NO"}
                      </span>
                    </p>
                    <p className="text-slate-500 text-[10px]">
                      IF score: {Number(preview.if_score).toFixed(4)}
                    </p>
                  </div>
                ) : (
                  <p className="text-[11px] text-slate-600 font-mono">Computing…</p>
                )}
              </div>
            </div>
          )}

          {tab === "Compliance" && (
            <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] overflow-hidden">
              <div className="px-4 py-3 border-b border-white/5">
                <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase">
                  CIS AWS Benchmark — IAM Violations
                </h3>
              </div>
              <div className="overflow-x-auto max-h-[520px] overflow-y-auto">
                <table className="w-full text-[11px] font-mono">
                  <thead className="sticky top-0 bg-[#0f1629] text-[9px] uppercase tracking-widest text-slate-500 border-b border-white/5">
                    <tr>
                      <th className="text-left px-4 py-2">Role</th>
                      <th className="text-left px-2 py-2">Rule</th>
                      <th className="text-left px-2 py-2">Severity</th>
                      <th className="text-left px-4 py-2">Detail</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compliance.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-slate-600">
                          No violations detected for current graph.
                        </td>
                      </tr>
                    )}
                    {compliance.map((v, i) => (
                      <tr key={`${v.role_arn}-${i}`} className="border-t border-white/5">
                        <td className="px-4 py-2 text-slate-200 max-w-[180px] truncate" title={v.role_name}>
                          {v.role_name}
                        </td>
                        <td className="px-2 py-2 text-slate-400">{v.rule_id}</td>
                        <td className="px-2 py-2 text-amber-400">{v.severity}</td>
                        <td className="px-4 py-2 text-slate-500 text-[10px]">{v.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>
      <HealthStatus health={health} />
    </div>
  );
}
