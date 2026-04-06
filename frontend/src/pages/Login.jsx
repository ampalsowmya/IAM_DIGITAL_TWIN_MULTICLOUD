import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const body = new URLSearchParams();
      body.append("username", username);
      body.append("password", password);
      const res = await axios.post(`${baseURL}/auth/token`, body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("token", res.data.access_token);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0e1a] px-4">
      <div className="w-full max-w-md rounded-xl border border-[rgba(99,179,237,0.15)] bg-[#0f1629] p-8 shadow-card">
        <div className="flex items-center gap-3 mb-8">
          <div className="h-12 w-12 rounded-lg bg-blue-500/20 border border-blue-400/40 flex items-center justify-center">
            <svg
              className="w-7 h-7 text-sky-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeWidth="1.5"
                d="M12 3l8 4v10l-8 4-8-4V7l8-4z"
                strokeLinejoin="round"
              />
              <path strokeWidth="1.5" d="M12 12l8-4M12 12v10M12 12L4 8" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-widest text-white font-sans">
              IAM DIGITAL TWIN
            </h1>
            <p className="text-[10px] tracking-[0.25em] text-slate-400 uppercase">
              AI Risk Intelligence Platform
            </p>
          </div>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-[10px] uppercase tracking-widest text-slate-500 mb-1">
              Username
            </label>
            <input
              className="w-full rounded-md bg-[#0a0e1a] border border-white/10 px-3 py-2 text-sm font-mono text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500/60"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-widest text-slate-500 mb-1">
              Password
            </label>
            <input
              type="password"
              className="w-full rounded-md bg-[#0a0e1a] border border-white/10 px-3 py-2 text-sm font-mono text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500/60"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {error && (
            <p className="text-sm text-red-400 font-mono" role="alert">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-md bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold tracking-widest uppercase disabled:opacity-50"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
