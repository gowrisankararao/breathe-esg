import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Database,
  FileWarning,
  Lock,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type DashboardStats } from "../api";

const SOURCE_LABELS: Record<string, string> = {
  sap: "SAP",
  utility: "Utility",
  travel: "Travel",
};

const SCOPE_LABELS: Record<string, string> = {
  scope1: "Scope 1",
  scope2: "Scope 2",
  scope3: "Scope 3",
};

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboard().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-breathe-500 border-t-transparent" />
      </div>
    );
  }

  if (!stats) return null;

  const cards = [
    {
      label: "Pending review",
      value: stats.pending_review,
      icon: Clock,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      link: "/review?review_status=pending",
    },
    {
      label: "Flagged suspicious",
      value: stats.suspicious,
      icon: AlertTriangle,
      color: "text-orange-400",
      bg: "bg-orange-500/10",
      link: "/review?is_suspicious=true",
    },
    {
      label: "Approved",
      value: stats.approved,
      icon: CheckCircle2,
      color: "text-breathe-400",
      bg: "bg-breathe-500/10",
      link: "/review?review_status=approved",
    },
    {
      label: "Locked for audit",
      value: stats.locked,
      icon: Lock,
      color: "text-slate-400",
      bg: "bg-slate-500/10",
      link: "/review?review_status=locked",
    },
  ];

  return (
    <div>
      <header className="mb-8">
        <h1 className="font-display text-3xl font-semibold text-white">
          Review dashboard
        </h1>
        <p className="mt-1 text-slate-400">
          {stats.total_activities} normalized activity records across all sources
        </p>
      </header>

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(({ label, value, icon: Icon, color, bg, link }) => (
          <Link key={label} to={link} className="card group p-5 transition hover:border-breathe-600/30">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">{label}</p>
                <p className="mt-1 font-display text-3xl font-semibold text-white">
                  {value}
                </p>
              </div>
              <div className={`rounded-xl p-2.5 ${bg}`}>
                <Icon className={`h-5 w-5 ${color}`} />
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h2 className="mb-4 flex items-center gap-2 font-semibold text-white">
            <Database className="h-4 w-4 text-breathe-400" />
            By source
          </h2>
          <div className="space-y-3">
            {Object.entries(stats.by_source).map(([key, count]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm text-slate-300">
                  {SOURCE_LABELS[key] || key}
                </span>
                <div className="flex items-center gap-3">
                  <div className="h-2 w-32 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-breathe-500"
                      style={{
                        width: `${(count / stats.total_activities) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="w-8 text-right text-sm font-medium text-white">
                    {count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h2 className="mb-4 font-semibold text-white">By GHG scope</h2>
          <div className="space-y-3">
            {Object.entries(stats.by_scope).map(([key, count]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm text-slate-300">
                  {SCOPE_LABELS[key] || key}
                </span>
                <span className="text-sm font-medium text-white">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card mt-6 p-6">
        <h2 className="mb-4 flex items-center gap-2 font-semibold text-white">
          <FileWarning className="h-4 w-4 text-amber-400" />
          Recent ingestion runs
        </h2>
        {stats.recent_runs.length === 0 ? (
          <p className="text-sm text-slate-500">
            No ingestions yet.{" "}
            <Link to="/upload" className="text-breathe-400 hover:underline">
              Upload data
            </Link>
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500">
                  <th className="pb-3 pr-4 font-medium">Source</th>
                  <th className="pb-3 pr-4 font-medium">File</th>
                  <th className="pb-3 pr-4 font-medium">Parsed</th>
                  <th className="pb-3 pr-4 font-medium">Failed</th>
                  <th className="pb-3 font-medium">Suspicious</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_runs.map((run) => (
                  <tr key={run.id} className="border-b border-slate-800/50">
                    <td className="py-3 pr-4 capitalize text-slate-200">
                      {SOURCE_LABELS[run.source_type] || run.source_type}
                    </td>
                    <td className="py-3 pr-4 text-slate-400">{run.filename}</td>
                    <td className="py-3 pr-4 text-breathe-400">{run.rows_parsed}</td>
                    <td className="py-3 pr-4 text-red-400">{run.rows_failed}</td>
                    <td className="py-3 text-amber-400">{run.rows_suspicious}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
