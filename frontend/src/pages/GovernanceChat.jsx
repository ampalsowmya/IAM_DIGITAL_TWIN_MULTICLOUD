import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { apiClient } from "../api/client";

export default function GovernanceChat() {
  const [q, setQ] = useState("Explain highest risk role");
  const [messages, setMessages] = useState([]);
  const quick = ["Explain highest risk role", "Suggest least-privilege for AdminRole", "Show ISO 27001 gaps"];
  const send = async (text) => {
    const intent = text.toLowerCase().includes("suggest") ? "recommend" : "explain";
    const payload = { identity_name: "Unknown", risk_score: 70, permissions: ["*"] };
    const res = intent === "recommend" ? await apiClient.governanceRecommend(payload) : await apiClient.governanceExplain(payload);
    setMessages((m) => [...m, { role: "user", text }, { role: "assistant", text: res.data.response || JSON.stringify(res.data) }]);
  };
  return <div className="card space-y-3">
    <div className="flex gap-2 flex-wrap">{quick.map((p)=><button key={p} className="btn" onClick={()=>send(p)}>{p}</button>)}</div>
    <div className="h-80 overflow-auto space-y-2">{messages.map((m,i)=><div key={i} className="p-2 rounded bg-slate-900"><b>{m.role}:</b> <ReactMarkdown>{m.text}</ReactMarkdown></div>)}</div>
    <div className="flex gap-2"><input className="input flex-1" value={q} onChange={(e)=>setQ(e.target.value)} /><button className="btn" onClick={()=>send(q)}>Send</button></div>
  </div>;
}

