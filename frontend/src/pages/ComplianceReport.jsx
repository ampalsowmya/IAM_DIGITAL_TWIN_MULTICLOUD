import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client";

export default function ComplianceReport() {
  const [fw, setFw] = useState("ISO 27001");
  const [report, setReport] = useState({ controls: [] });
  useEffect(() => { apiClient.complianceReport(fw).then((r) => setReport(r.data)); }, [fw]);
  const score = useMemo(() => {
    const c = report.controls || [];
    if (!c.length) return 0;
    const pts = c.reduce((a, x) => a + (x.status === "PASS" ? 1 : x.status === "PARTIAL" ? 0.5 : 0), 0);
    return Math.round((pts / c.length) * 100);
  }, [report]);
  return <div className="card space-y-3">
    <div className="flex gap-2">{["ISO 27001","NIST CSF","SOC2"].map((f)=><button key={f} onClick={()=>setFw(f)} className={`btn ${fw===f?"!bg-cyan-700":""}`}>{f}</button>)}</div>
    <div className="w-full bg-slate-700 rounded h-3"><div className="bg-cyan-400 h-3 rounded" style={{width:`${score}%`}} /></div>
    <div>Overall compliance score: {score}%</div>
    <table className="w-full text-sm"><thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Affected</th><th>Hint</th></tr></thead><tbody>{(report.controls||[]).map((c)=><tr key={c.id}><td>{c.id}</td><td>{c.name}</td><td>{c.status}</td><td>{(c.affected_identities||[]).length}</td><td>{c.remediation_hint}</td></tr>)}</tbody></table>
    <button className="btn" onClick={()=>window.print()}>Export as PDF</button>
  </div>;
}

