import { Link, useLocation } from "react-router-dom";

const links = [
  ["/", "Dashboard"],
  ["/graph", "Graph Explorer"],
  ["/escalation", "Escalation Paths"],
  ["/risk", "Risk Scoring"],
  ["/whatif", "What-If"],
  ["/governance", "Governance Chat"],
  ["/compliance", "Compliance Report"],
  ["/remediation", "Remediation"],
];

export default function Layout({ children }) {
  const { pathname } = useLocation();
  return (
    <div className="min-h-screen bg-[#0a0e1a] text-slate-100 flex">
      <aside className="w-64 border-r border-cyan-500/20 p-4 hidden md:block">
        <h1 className="font-['Syne'] text-xl mb-6">IAM Twin</h1>
        <nav className="space-y-2">
          {links.map(([to, label]) => (
            <Link key={to} to={to} className={`block px-3 py-2 rounded ${pathname === to ? "bg-cyan-500/20 text-cyan-300" : "hover:bg-slate-800"}`}>
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-4">{children}</main>
    </div>
  );
}

