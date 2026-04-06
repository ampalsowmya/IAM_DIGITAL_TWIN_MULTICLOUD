import { useEffect, useState } from "react";

export default function LiveBadge() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const utc = now.toISOString().replace("T", " ").slice(0, 19);

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400 animate-live-pulse" />
        </span>
        <span className="text-[10px] font-mono font-semibold tracking-widest text-emerald-400">
          LIVE
        </span>
      </div>
      <div className="text-[11px] font-mono text-slate-400 tabular-nums">{utc} UTC</div>
    </div>
  );
}
