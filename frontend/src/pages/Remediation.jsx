import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

export default function Remediation() {
  const [items, setItems] = useState([]);
  const [toast, setToast] = useState("");
  const load = () => apiClient.remediationSuggestions().then((r) => setItems(r.data || []));
  useEffect(() => { load(); }, []);
  return <div className="space-y-3">
    {toast && <div className="card">{toast}</div>}
    {items.map((i, idx)=><div key={idx} className="card flex justify-between items-center"><div><div className="font-bold">{i.identity_name}</div><div>{i.action} | risk reduction: {i.estimated_risk_reduction}</div></div><button className="btn" onClick={async()=>{const r=await apiClient.remediationApply(i, true);setToast(r.data.status);}}>Apply</button></div>)}
  </div>;
}

