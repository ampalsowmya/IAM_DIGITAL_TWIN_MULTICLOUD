import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

export default function WhatIf() {
  const [scores, setScores] = useState([]);
  const [identity, setIdentity] = useState("");
  const [permission, setPermission] = useState("s3:*");
  const [type, setType] = useState("remove");
  const [result, setResult] = useState(null);
  useEffect(() => { apiClient.riskScores().then((r) => setScores(r.data || [])); }, []);
  return <div className="grid md:grid-cols-2 gap-4">
    <div className="card space-y-2">
      <select className="input" value={identity} onChange={(e)=>setIdentity(e.target.value)}>{scores.map((s)=><option key={s.identity_id} value={s.identity_id}>{s.identity_name}</option>)}</select>
      <select className="input" value={type} onChange={(e)=>setType(e.target.value)}><option value="add">add</option><option value="remove">remove</option></select>
      <input className="input" value={permission} onChange={(e)=>setPermission(e.target.value)} />
      <button className="btn" onClick={async ()=>setResult((await apiClient.whatIf({identity_id: identity, proposed_changes:[{type,permission,resource:"*"}]})).data)}>Simulate</button>
      <button className="btn" onClick={async ()=>result && apiClient.remediationApply({identity_id:identity, action:"restrict_resource"}, true)}>Apply Changes</button>
    </div>
    <div className="card"><pre className="text-xs whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre></div>
  </div>;
}

