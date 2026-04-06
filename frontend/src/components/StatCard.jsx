export default function StatCard({ title, value, subtitle, borderClass }) {
  return (
    <div
      className={`rounded-lg border bg-[#0f1629] p-4 shadow-card border-t-2 ${borderClass} border-x border-b border-[rgba(99,179,237,0.12)]`}
    >
      <p className="text-[9px] font-semibold tracking-[0.2em] text-slate-500 uppercase mb-2">
        {title}
      </p>
      <p className="text-3xl font-mono font-semibold tabular-nums leading-none">{value}</p>
      {subtitle && (
        <p className="mt-2 text-[10px] text-slate-500 font-mono">{subtitle}</p>
      )}
    </div>
  );
}
