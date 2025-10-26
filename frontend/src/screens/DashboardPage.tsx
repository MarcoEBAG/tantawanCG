import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api/client";

interface HealthResponse {
  status: string;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<HealthResponse>("/health")
      .then((data) => setHealth(data))
      .catch((err) => setError(err.message ?? "Fehler beim Laden"));
  }, []);

  function handleLogout() {
    localStorage.removeItem("authToken");
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-slate-100 p-4">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Übersicht</h1>
          <p className="text-sm text-slate-500">Restaurant Cockpit</p>
        </div>

        <button
          onClick={handleLogout}
          className="rounded-xl bg-white border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 shadow hover:bg-slate-50"
        >
          Logout
        </button>
      </header>

      <main className="grid gap-4 md:grid-cols-3">
        <div className="bg-white rounded-2xl p-4 shadow border border-slate-200">
          <div className="text-sm text-slate-500 mb-1">API Status</div>
          {error && (
            <div className="text-red-600 text-sm mb-1">
              {error}
            </div>
          )}
          {health ? (
            <div className="text-2xl font-semibold text-slate-900">
              {health.status}
            </div>
          ) : !error ? (
            <div className="text-slate-400 text-sm">Lade…</div>
          ) : null}
          <div className="text-xs text-slate-400">/health vom Backend</div>
        </div>

        <div className="bg-white rounded-2xl p-4 shadow border border-slate-200">
          <div className="text-sm text-slate-500 mb-1">
            Bestellungen heute
          </div>
          <div className="text-2xl font-semibold text-slate-900">0</div>
          <div className="text-xs text-slate-400">
            API-Endpoint später anbinden
          </div>
        </div>

        <div className="bg-white rounded-2xl p-4 shadow border border-slate-200">
          <div className="text-sm text-slate-500 mb-1">
            Verfügbarkeit
          </div>
          <div className="text-2xl font-semibold text-slate-900">
            offen
          </div>
          <div className="text-xs text-slate-400">
            Tischplan kommt noch
          </div>
        </div>
      </main>
    </div>
  );
}
