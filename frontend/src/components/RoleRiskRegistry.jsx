const FILTER_ALL = "all";
const FILTER_CRITICAL = "critical";
const FILTER_HIGH = "high";
const FILTER_ANOMALIES = "anomalies";

function cloudBadge(cloud) {
  const c = (cloud || "aws").toLowerCase();
  if (c === "azure" || c === "az")
    return { label: "AZURE", className: "bg-purple-500/20 text-purple-300 border-purple-500/40" };
  if (c === "gcp")
    return { label: "GCP", className: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" };
  return { label: "AWS", className: "bg-orange-500/15 text-orange-300 border-orange-500/35" };
}

function levelBadge(level) {
  const u = (level || "").toUpperCase();
  if (u === "CRITICAL")
    return "bg-red-500/20 text-red-400 border-red-500/40";
  if (u === "HIGH") return "bg-orange-500/20 text-orange-300 border-orange-500/40";
  if (u === "MEDIUM") return "bg-yellow-500/15 text-yellow-300 border-yellow-500/35";
  return "bg-emerald-500/15 text-emerald-300 border-emerald-500/35";
}

export default function RoleRiskRegistry({ scores, filter, onFilterChange }) {
  const filtered = scores.filter((s) => {
    if (filter === FILTER_CRITICAL) return s.level === "CRITICAL";
    if (filter === FILTER_HIGH) return s.level === "HIGH";
    if (filter === FILTER_ANOMALIES) return s.anomaly;
    return true;
  });

  const filters = [
    [FILTER_ALL, "All"],
    [FILTER_CRITICAL, "Critical"],
    [FILTER_HIGH, "High"],
    [FILTER_ANOMALIES, "Anomalies"],
  ];

  return (
    <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] shadow-card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-white/5">
        <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase">
          Role Risk Registry
        </h3>
        <div className="flex flex-wrap gap-1">
          {filters.map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => onFilterChange(key)}
              className={`px-2.5 py-1 rounded text-[9px] font-mono uppercase tracking-wide border ${
                filter === key
                  ? "bg-sky-500/20 text-sky-300 border-sky-500/40"
                  : "bg-transparent text-slate-500 border-white/10 hover:border-white/20"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
        <table className="w-full text-left text-[11px] font-mono">
          <thead className="sticky top-0 bg-[#0f1629] z-10 text-[9px] uppercase tracking-widest text-slate-500 border-b border-white/5">
            <tr>
              <th className="px-4 py-2">Role</th>
              <th className="px-2 py-2">Cloud</th>
              <th className="px-2 py-2">Risk Score</th>
              <th className="px-2 py-2">Level</th>
              <th className="px-2 py-2">IF Score</th>
              <th className="px-2 py-2">Anomaly</th>
              <th className="px-2 py-2">Permissions</th>
              <th className="px-4 py-2">Escalation</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                  No roles match this filter.
                </td>
              </tr>
            )}
            {filtered.map((row) => {
              const cb = cloudBadge(row.cloud);
              const pct = Math.min(100, Number(row.risk_score) || 0);
              const barColor =
                row.level === "CRITICAL"
                  ? "bg-red-500"
                  : row.level === "HIGH"
                    ? "bg-orange-500"
                    : row.level === "MEDIUM"
                      ? "bg-yellow-500"
                      : "bg-emerald-500";
              return (
                <tr
                  key={row.identity_id}
                  className="border-b border-white/[0.04] hover:bg-white/[0.03] transition-colors"
                >
                  <td className="px-4 py-2 text-slate-200 max-w-[200px] truncate" title={row.name}>
                    {row.name}
                  </td>
                  <td className="px-2 py-2">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-[9px] border ${cb.className}`}
                    >
                      {cb.label}
                    </span>
                  </td>
                  <td className="px-2 py-2 min-w-[120px]">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 rounded bg-slate-800 overflow-hidden min-w-[64px]">
                        <div className={`h-full ${barColor}`} style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-slate-300 tabular-nums w-8 text-right">{row.risk_score}</span>
                    </div>
                  </td>
                  <td className="px-2 py-2">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-[9px] border ${levelBadge(row.level)}`}
                    >
                      {row.level}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-purple-400 tabular-nums">
                    {Number(row.if_score).toFixed(3)}
                  </td>
                  <td className="px-2 py-2">
                    {row.anomaly ? (
                      <span className="inline-block px-2 py-0.5 rounded-full text-[9px] bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse">
                        ANOMALY
                      </span>
                    ) : (
                      <span className="inline-block px-2 py-0.5 rounded-full text-[9px] bg-slate-700/40 text-slate-400 border border-white/10">
                        NORMAL
                      </span>
                    )}
                  </td>
                  <td className="px-2 py-2 text-slate-300 tabular-nums">{row.permissions_count}</td>
                  <td className="px-4 py-2 text-slate-400">
                    {row.escalation_paths > 0 ? `${row.escalation_paths} PATHS` : "NONE"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export { FILTER_ALL, FILTER_CRITICAL, FILTER_HIGH, FILTER_ANOMALIES };
