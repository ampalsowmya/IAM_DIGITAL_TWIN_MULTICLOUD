import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

export default function EscalationDonut({ scores }) {
  const norm = (c) => (c || "").toString().toLowerCase();
  const data = [
    {
      name: "AWS Critical",
      value: scores.filter(
        (s) => norm(s.cloud) === "aws" && s.level === "CRITICAL"
      ).length,
      color: "#ef4444",
    },
    {
      name: "AWS High",
      value: scores.filter((s) => norm(s.cloud) === "aws" && s.level === "HIGH").length,
      color: "#eab308",
    },
    {
      name: "Azure Critical",
      value: scores.filter(
        (s) => (norm(s.cloud) === "azure" || norm(s.cloud) === "az") && s.level === "CRITICAL"
      ).length,
      color: "#a855f7",
    },
    {
      name: "GCP Low",
      value: scores.filter(
        (s) => norm(s.cloud) === "gcp" && s.level === "LOW"
      ).length,
      color: "#22c55e",
    },
  ];

  const total = data.reduce((a, b) => a + b.value, 0) || 1;

  return (
    <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] p-4 shadow-card h-[320px] flex flex-col">
      <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase mb-2">
        Escalation Risk by Cloud
      </h3>
      <div className="flex-1 min-h-0 flex flex-row">
        <div className="flex-1 min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                innerRadius={58}
                outerRadius={88}
                paddingAngle={2}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} stroke="rgba(15,22,41,0.9)" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip
                formatter={(v) => [v, "Roles"]}
                contentStyle={{
                  background: "#0f1629",
                  border: "1px solid rgba(99,179,237,0.2)",
                  borderRadius: 8,
                  fontSize: 11,
                  fontFamily: "JetBrains Mono",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="w-40 flex flex-col justify-center gap-2 text-[9px] font-mono pl-2">
          {data.map((d) => (
            <div key={d.name} className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-sm shrink-0" style={{ background: d.color }} />
              <span className="text-slate-400 truncate">{d.name}</span>
              <span className="text-slate-200 ml-auto tabular-nums">{d.value}</span>
            </div>
          ))}
          <p className="text-[8px] text-slate-600 mt-2">Roles in view: {total}</p>
        </div>
      </div>
    </div>
  );
}
