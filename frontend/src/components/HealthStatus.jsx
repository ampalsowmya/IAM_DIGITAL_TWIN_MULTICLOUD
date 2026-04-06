import { useState } from "react";

export default function HealthStatus({ health }) {
  const [open, setOpen] = useState(false);

  const aws = health?.aws;
  const neo = health?.neo4j;
  const ml = health?.ml_models;
  const details = health?.details || {};

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full rounded-lg border border-[rgba(99,179,237,0.2)] bg-[#0f1629]/95 backdrop-blur px-3 py-2 text-left shadow-card hover:border-sky-500/40 transition-colors"
      >
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] font-mono text-slate-300">
          <span>
            AWS: {aws ? "✅" : "❌"}
          </span>
          <span className="text-slate-600">|</span>
          <span>
            Neo4j: {neo ? "✅" : "❌"}
          </span>
          <span className="text-slate-600">|</span>
          <span>
            ML: {ml ? "✅" : "❌"}
          </span>
          <span className="ml-auto text-[9px] text-slate-500">{open ? "▼" : "▲"}</span>
        </div>
      </button>
      {open && (
        <div className="mt-2 rounded-lg border border-[rgba(99,179,237,0.15)] bg-[#0a0e1a]/98 p-3 text-[10px] font-mono text-slate-400 max-h-48 overflow-y-auto">
          {Object.keys(details).length === 0 && <p className="text-slate-500">No error details.</p>}
          {Object.entries(details).map(([k, v]) => (
            <p key={k} className="mb-1 break-words">
              <span className="text-slate-500">{k}: </span>
              {String(v)}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
