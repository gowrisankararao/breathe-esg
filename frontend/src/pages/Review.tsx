import {
  AlertTriangle,
  Check,
  ChevronRight,
  Lock,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type Activity } from "../api";

const SOURCE_LABELS: Record<string, string> = {
  sap: "SAP",
  utility: "Utility",
  travel: "Travel",
};

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-amber-500/15 text-amber-300",
    approved: "bg-breathe-500/15 text-breathe-300",
    rejected: "bg-red-500/15 text-red-300",
    locked: "bg-slate-500/15 text-slate-300",
  };
  return (
    <span className={`badge ${styles[status] || styles.pending}`}>
      {status}
    </span>
  );
}

export default function Review() {
  const [params, setParams] = useSearchParams();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [selected, setSelected] = useState<Activity | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState("");

  const filters = {
    review_status: params.get("review_status") || "",
    is_suspicious: params.get("is_suspicious") || "",
    source_type: params.get("source_type") || "",
  };

  const load = useCallback(() => {
    setLoading(true);
    const q: Record<string, string> = {};
    if (filters.review_status) q.review_status = filters.review_status;
    if (filters.is_suspicious) q.is_suspicious = filters.is_suspicious;
    if (filters.source_type) q.source_type = filters.source_type;
    api
      .activities(q)
      .then((data) => setActivities(data.results))
      .finally(() => setLoading(false));
  }, [filters.review_status, filters.is_suspicious, filters.source_type]);

  useEffect(() => {
    load();
  }, [load]);

  async function openDetail(id: number) {
    const detail = await api.activity(id);
    setSelected(detail);
    setNotes("");
  }

  async function handleReview(action: string) {
    if (!selected) return;
    await api.review(selected.id, action, notes);
    setSelected(null);
    load();
  }

  async function handleBulk(action: string) {
    if (selectedIds.size === 0) return;
    await api.bulkReview([...selectedIds], action, notes);
    setSelectedIds(new Set());
    load();
  }

  function toggleSelect(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold text-white">
            Review queue
          </h1>
          <p className="mt-1 text-slate-400">
            Approve normalized rows before they lock for audit
          </p>
        </div>
        {selectedIds.size > 0 && (
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-primary"
              onClick={() => handleBulk("approve")}
            >
              Approve {selectedIds.size}
            </button>
            <button
              type="button"
              className="btn-danger"
              onClick={() => handleBulk("reject")}
            >
              Reject
            </button>
          </div>
        )}
      </header>

      <div className="mb-4 flex flex-wrap gap-2">
        {[
          { key: "review_status", value: "", label: "All statuses" },
          { key: "review_status", value: "pending", label: "Pending" },
          { key: "is_suspicious", value: "true", label: "Suspicious" },
          { key: "source_type", value: "sap", label: "SAP" },
          { key: "source_type", value: "utility", label: "Utility" },
          { key: "source_type", value: "travel", label: "Travel" },
        ].map((f) => {
          const active =
            (f.key === "review_status" && filters.review_status === f.value) ||
            (f.key === "is_suspicious" && filters.is_suspicious === f.value) ||
            (f.key === "source_type" && filters.source_type === f.value);
          return (
            <button
              key={f.label}
              type="button"
              onClick={() => {
                const next = new URLSearchParams();
                if (f.value) next.set(f.key, f.value);
                setParams(next);
              }}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                active
                  ? "bg-breathe-600/20 text-breathe-300"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex h-48 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-breathe-500 border-t-transparent" />
          </div>
        ) : activities.length === 0 ? (
          <p className="p-8 text-center text-slate-500">No records match filters</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-500">
                <th className="w-10 p-4" />
                <th className="p-4 font-medium">Date</th>
                <th className="p-4 font-medium">Source</th>
                <th className="p-4 font-medium">Category</th>
                <th className="p-4 font-medium">Description</th>
                <th className="p-4 font-medium">Qty</th>
                <th className="p-4 font-medium">Status</th>
                <th className="w-10 p-4" />
              </tr>
            </thead>
            <tbody>
              {activities.map((a) => (
                <tr
                  key={a.id}
                  className="border-b border-slate-800/50 transition hover:bg-slate-800/30"
                >
                  <td className="p-4">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(a.id)}
                      onChange={() => toggleSelect(a.id)}
                      className="rounded border-slate-600"
                    />
                  </td>
                  <td className="p-4 text-slate-300">{a.activity_date || "—"}</td>
                  <td className="p-4">
                    <span className="text-slate-200">
                      {SOURCE_LABELS[a.source_type]}
                    </span>
                    {a.is_suspicious && (
                      <AlertTriangle className="ml-1 inline h-3.5 w-3.5 text-amber-400" />
                    )}
                  </td>
                  <td className="p-4 capitalize text-slate-400">{a.category}</td>
                  <td className="max-w-xs truncate p-4 text-slate-300">
                    {a.description || a.site_name}
                  </td>
                  <td className="p-4 text-slate-400">
                    {a.quantity
                      ? `${a.quantity} ${a.unit_normalized || ""}`
                      : "—"}
                  </td>
                  <td className="p-4">
                    <StatusBadge status={a.review_status} />
                  </td>
                  <td className="p-4">
                    <button
                      type="button"
                      onClick={() => openDetail(a.id)}
                      className="text-slate-500 hover:text-breathe-400"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
          <div className="card h-full w-full max-w-lg overflow-y-auto rounded-none border-l border-slate-800 p-6">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">
                  Record #{selected.id}
                </p>
                <h2 className="font-display text-xl font-semibold text-white">
                  {selected.description || "Activity detail"}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="text-slate-500 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <dl className="space-y-3 text-sm">
              {[
                ["Scope", selected.scope],
                ["Category", selected.category],
                ["Site", selected.site_name || selected.plant_code],
                ["Date", selected.activity_date],
                [
                  "Period",
                  selected.period_start
                    ? `${selected.period_start} → ${selected.period_end}`
                    : null,
                ],
                [
                  "Quantity",
                  selected.quantity_normalized
                    ? `${selected.quantity_normalized} ${selected.unit_normalized}`
                    : null,
                ],
                [
                  "Amount",
                  selected.amount
                    ? `${selected.currency} ${selected.amount}`
                    : null,
                ],
                [
                  "Route",
                  selected.origin || selected.destination
                    ? `${selected.origin || "?"} → ${selected.destination || "?"}`
                    : null,
                ],
                ["Reference", selected.source_reference],
              ]
                .filter(([, v]) => v)
                .map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-4">
                    <dt className="text-slate-500">{k}</dt>
                    <dd className="text-right text-slate-200">{v}</dd>
                  </div>
                ))}
            </dl>

            {selected.suspicion_reasons?.length > 0 && (
              <div className="mt-4 rounded-xl bg-amber-500/10 p-4">
                <p className="mb-2 text-xs font-medium uppercase text-amber-400">
                  Suspicion flags
                </p>
                <ul className="space-y-1 text-sm text-amber-200/90">
                  {selected.suspicion_reasons.map((r) => (
                    <li key={r}>• {r.replace(/_/g, " ")}</li>
                  ))}
                </ul>
              </div>
            )}

            {selected.audit_logs && selected.audit_logs.length > 0 && (
              <div className="mt-6">
                <p className="mb-2 text-xs font-medium uppercase text-slate-500">
                  Audit trail
                </p>
                <div className="space-y-2">
                  {selected.audit_logs.map((log) => (
                    <div
                      key={log.id}
                      className="rounded-lg bg-slate-800/40 px-3 py-2 text-xs"
                    >
                      <span className="font-medium text-slate-300">
                        {log.action}
                      </span>
                      <span className="text-slate-500"> — {log.performed_by_name}</span>
                      <p className="text-slate-500">{log.note}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selected.review_status !== "locked" && (
              <div className="mt-6 space-y-3 border-t border-slate-800 pt-6">
                <textarea
                  className="input min-h-[80px]"
                  placeholder="Review notes (optional)"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="btn-primary flex-1"
                    onClick={() => handleReview("approve")}
                  >
                    <Check className="h-4 w-4" />
                    Approve
                  </button>
                  <button
                    type="button"
                    className="btn-danger"
                    onClick={() => handleReview("reject")}
                  >
                    Reject
                  </button>
                  {selected.review_status === "approved" && (
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => handleReview("lock")}
                    >
                      <Lock className="h-4 w-4" />
                      Lock for audit
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
