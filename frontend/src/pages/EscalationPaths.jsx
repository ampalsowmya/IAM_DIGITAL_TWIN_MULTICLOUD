import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

export default function EscalationPaths() {
  const [rows, setRows] = useState([]);
  useEffect(() => { apiClient.escalationPaths().then((r) => setRows(r.data || [])); }, []);
  const color = (r) => r === "CRITICAL" ? "text-red-400" : r === "HIGH" ? "text-orange-400" : "text-yellow-300";
  return <div className="card overflow-auto"><table className="w-full text-sm"><thead><tr><th>Source</th><th>Target</th><th>Length</th><th>Risk</th></tr></thead><tbody>{rows.map((r, i)=><tr key={i}><td>{r.source_identity}</td><td>{r.target_privilege}</td><td>{r.path_length}</td><td className={color(r.risk_level)}>{r.risk_level}</td></tr>)}</tbody></table></div>;
}

