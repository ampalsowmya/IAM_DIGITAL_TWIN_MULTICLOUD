import { useState } from "react";

function dotColor(level) {
  const u = (level || "").toUpperCase();
  if (u === "CRITICAL") return "bg-red-500";
  if (u === "HIGH") return "bg-orange-500";
  if (u === "MEDIUM") return "bg-yellow-500";
  return "bg-emerald-500";
}

export default function Sidebar({ scores, lastScan, ingestBusy, onRunIngest }) {
  const [cloud, setCloud] = useState("all");

  return (
    <aside className="w-[240px] shrink-0 border-r border-[rgba(99,179,237,0.12)] bg-[#0a0e1a] flex flex-col h-full">
      <div className="p-4 border-b border-white/5">
        <h2 className="text-[9px] font-bold tracking-[0.25em] text-slate-500 uppercase mb-3">
          IAM Roles
        </h2>
        <div className="space-y-2 max-h-[40vh] overflow-y-auto pr-1">
          {scores.length === 0 && (
            <p className="text-[10px] text-slate-600 font-mono">No roles ingested yet.</p>
          )}
          {scores.slice(0, 40).map((r) => (
            <div
              key={r.identity_id}
              className="flex items-center justify-between gap-2 rounded border border-white/5 bg-[#0f1629] px-2 py-1.5"
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className={`h-2 w-2 rounded-full shrink-0 ${dotColor(r.level)}`} />
                <span className="text-[10px] font-mono text-slate-300 truncate" title={r.name}>
                  {r.name}
                </span>
              </div>
              <span className="text-[9px] font-mono text-sky-400 tabular-nums shrink-0">
                {r.risk_score}
              </span>
            </div>
          ))}
        </div>
      </div>
      <div className="p-4 mt-auto border-t border-white/5 space-y-3">
        <div>
          <label className="block text-[9px] tracking-[0.2em] text-slate-500 uppercase mb-1">
            Active Cloud
          </label>
          <select
            className="w-full rounded bg-[#0f1629] border border-white/10 text-[10px] font-mono text-slate-200 px-2 py-1.5"
            value={cloud}
            onChange={(e) => {
              const v = e.target.value;
              setCloud(v);
              if (v !== "all") onRunIngest(v);
            }}
          >
            <option value="all">All Clouds</option>
            <option value="aws">AWS</option>
            <option value="azure">Azure</option>
            <option value="gcp">GCP</option>
          </select>
        </div>
        <button
          type="button"
          disabled={ingestBusy}
          onClick={() => onRunIngest(cloud)}
          className="w-full py-2 rounded text-[9px] font-semibold tracking-widest uppercase bg-sky-600/80 hover:bg-sky-500 disabled:opacity-50"
        >
          {ingestBusy ? "Syncing…" : "Run ingest"}
        </button>
        <div>
          <p className="text-[9px] tracking-[0.2em] text-slate-500 uppercase mb-1">Last scan</p>
          <p className="text-[10px] font-mono text-slate-400">{lastScan || "—"}</p>
        </div>
      </div>
    </aside>
  );
}
