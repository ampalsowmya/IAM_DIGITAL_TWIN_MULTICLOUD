import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function bucketLabel(i) {
  const lo = i * 10;
  const hi = lo + 10;
  return `${lo}-${hi}`;
}

export default function RiskDistributionChart({ scores }) {
  const buckets = Array.from({ length: 10 }, (_, i) => ({
    name: bucketLabel(i),
    count: 0,
  }));
  for (const s of scores) {
    const idx = Math.min(9, Math.floor(Number(s.risk_score) / 10));
    buckets[idx].count += 1;
  }

  return (
    <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] p-4 shadow-card h-[320px] flex flex-col">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase">
            Risk Score Distribution
          </h3>
          <p className="text-[9px] text-slate-600 font-mono mt-0.5">
            RandomForest + XGBoost
          </p>
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={buckets} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" />
                <stop offset="100%" stopColor="#a855f7" />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fill: "#64748b", fontSize: 9, fontFamily: "JetBrains Mono" }}
              axisLine={{ stroke: "rgba(148,163,184,0.15)" }}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: "#64748b", fontSize: 9, fontFamily: "JetBrains Mono" }}
              axisLine={{ stroke: "rgba(148,163,184,0.15)" }}
            />
            <Tooltip
              contentStyle={{
                background: "#0f1629",
                border: "1px solid rgba(99,179,237,0.2)",
                borderRadius: 8,
                fontSize: 11,
                fontFamily: "JetBrains Mono",
              }}
              labelStyle={{ color: "#94a3b8" }}
            />
            <Bar dataKey="count" fill="url(#barGrad)" radius={[4, 4, 0, 0]} maxBarSize={36} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
