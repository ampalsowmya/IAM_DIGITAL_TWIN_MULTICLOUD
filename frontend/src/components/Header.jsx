import LiveBadge from "./LiveBadge.jsx";

export default function Header({ activeTab, onTabChange }) {
  const tabs = [
    "Overview",
    "ML Models",
    "Anomaly Detection",
    "What-If Sim",
    "Compliance",
  ];

  return (
    <header className="border-b border-[rgba(99,179,237,0.12)] bg-[#0a0e1a]/95 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3 min-w-[220px]">
          <div className="h-10 w-10 rounded-lg bg-blue-500/15 border border-blue-400/30 flex items-center justify-center shrink-0">
            <svg
              className="w-6 h-6 text-sky-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeWidth="1.5"
                d="M12 3l8 4v10l-8 4-8-4V7l8-4z"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white leading-tight">
              IAM Digital Twin
            </h1>
            <p className="text-[9px] tracking-[0.2em] text-slate-500 uppercase">
              AI Risk Intelligence Platform
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {[
            { label: "AWS", color: "bg-orange-500" },
            { label: "Azure", color: "bg-purple-500" },
            { label: "GCP", color: "bg-emerald-500" },
          ].map((c) => (
            <span
              key={c.label}
              className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-[#0f1629] px-2.5 py-1 text-[10px] font-mono tracking-wide text-slate-300"
            >
              <span className={`h-1.5 w-1.5 rounded-full ${c.color}`} />
              {c.label}
            </span>
          ))}
        </div>
        <LiveBadge />
      </div>
      <nav className="flex gap-1 px-6 border-t border-white/5">
        {tabs.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => onTabChange(t)}
            className={`px-4 py-2.5 text-[10px] font-semibold tracking-[0.15em] uppercase border-b-2 -mb-px transition-colors ${
              activeTab === t
                ? "text-sky-400 border-sky-500"
                : "text-slate-500 border-transparent hover:text-slate-300"
            }`}
          >
            {t}
          </button>
        ))}
      </nav>
    </header>
  );
}
