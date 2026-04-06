export default function CloudBadge({ cloud }) {
  const color = cloud === "aws" ? "bg-orange-500" : cloud === "azure" ? "bg-blue-500" : "bg-green-500";
  return <span className={`px-2 py-1 rounded text-xs ${color}`}>{cloud?.toUpperCase()}</span>;
}

