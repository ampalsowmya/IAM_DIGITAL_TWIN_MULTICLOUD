import { useEffect, useState } from "react";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { apiClient } from "../api/client";
import RiskBadge from "../components/RiskBadge";

export default function RiskScoring() {
  const [scores, setScores] = useState([]);
  const [modal, setModal] = useState(null);
  useEffect(() => { apiClient.riskScores().then((r) => setScores(r.data || [])); }, []);
  return <div className="space-y-4">
    <div className="card overflow-auto"><table className="w-full text-sm"><thead><tr><th>Name</th><th>Cloud</th><th>Type</th><th>Risk</th><th>Anomaly</th><th>Factors</th></tr></thead><tbody>{scores.map((s)=><tr key={s.identity_id} onClick={async ()=>{const ex=(await apiClient.governanceExplain(s)).data;setModal({...s,ex});}}><td>{s.identity_name}</td><td>{s.cloud}</td><td>{s.type}</td><td><RiskBadge score={s.risk_score} /></td><td>{String(s.anomaly_flag)}</td><td>{(s.top_risk_factors||[]).join(", ")}</td></tr>)}</tbody></table></div>
    <div className="card h-64"><ResponsiveContainer><BarChart data={scores}><XAxis dataKey="identity_name" hide /><YAxis /><Tooltip /><Bar dataKey="risk_score" fill="#00d4ff" /></BarChart></ResponsiveContainer></div>
    {modal && <div className="fixed inset-0 bg-black/60 p-8" onClick={()=>setModal(null)}><div className="card max-w-2xl mx-auto"><h3>{modal.identity_name}</h3><pre className="text-xs">{JSON.stringify(modal.ex,null,2)}</pre></div></div>}
  </div>;
}

