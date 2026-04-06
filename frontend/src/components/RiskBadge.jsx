export default function RiskBadge({ score }) {
  const c = score > 80 ? "bg-red-500" : score > 60 ? "bg-orange-500" : "bg-yellow-500";
  return <span className={`px-2 py-1 rounded text-black text-xs ${c}`}>{score}</span>;
}

