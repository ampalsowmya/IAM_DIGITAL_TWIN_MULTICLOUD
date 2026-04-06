import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function PermissionHeatmap({ heatmap }) {
  const data = Object.entries(heatmap || {}).map(([name, value]) => ({
    name,
    value: Number(value) || 0,
  }));

  return (
    <div className="rounded-lg border border-[rgba(99,179,237,0.12)] bg-[#0f1629] p-4 shadow-card h-[280px]">
      <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400 uppercase mb-3">
        Permission Heatmap
      </h3>
      <div className="h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 4, right: 8, left: 4, bottom: 4 }}
          >
            <XAxis type="number" domain={[0, "dataMax + 1"]} hide />
            <YAxis
              type="category"
              dataKey="name"
              width={120}
              tick={{ fill: "#94a3b8", fontSize: 9, fontFamily: "JetBrains Mono" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "#0f1629",
                border: "1px solid rgba(99,179,237,0.2)",
                borderRadius: 8,
                fontSize: 11,
                fontFamily: "JetBrains Mono",
              }}
            />
            <Bar dataKey="value" fill="#f97316" radius={[0, 4, 4, 0]} barSize={14} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
