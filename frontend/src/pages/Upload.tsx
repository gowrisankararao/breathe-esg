import { FileUp, Fuel, Plane, Zap } from "lucide-react";
import { useState } from "react";
import { api } from "../api";

const SOURCES = [
  {
    id: "sap",
    label: "SAP — fuel & procurement",
    desc: "Semicolon-delimited flat file from custom SAP report (German/English headers)",
    icon: Fuel,
  },
  {
    id: "utility",
    label: "Utility portal — electricity",
    desc: "CSV billing export (meter, period, kWh, cost)",
    icon: Zap,
  },
  {
    id: "travel",
    label: "Concur — business travel",
    desc: "Pipe-delimited expense extract (flights, hotels, ground)",
    icon: Plane,
  },
];

export default function Upload() {
  const [source, setSource] = useState("sap");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const run = await api.upload(source, file);
      setResult(
        `Ingested ${run.rows_parsed} rows (${run.rows_failed} failed, ${run.rows_suspicious} flagged suspicious)`
      );
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <header className="mb-8">
        <h1 className="font-display text-3xl font-semibold text-white">
          Ingest data
        </h1>
        <p className="mt-1 text-slate-400">
          Upload source files — each is parsed, normalized, and queued for analyst review
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-3 mb-8">
        {SOURCES.map(({ id, label, desc, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setSource(id)}
            className={`card p-5 text-left transition ${
              source === id
                ? "border-breathe-500/50 ring-1 ring-breathe-500/30"
                : "hover:border-slate-700"
            }`}
          >
            <Icon
              className={`mb-3 h-6 w-6 ${
                source === id ? "text-breathe-400" : "text-slate-500"
              }`}
            />
            <p className="font-medium text-white">{label}</p>
            <p className="mt-1 text-xs text-slate-500">{desc}</p>
          </button>
        ))}
      </div>

      <div className="card p-8">
        <label
          className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-8 py-16 transition ${
            file
              ? "border-breathe-500/50 bg-breathe-500/5"
              : "border-slate-700 hover:border-slate-600"
          }`}
        >
          <FileUp className="mb-4 h-10 w-10 text-slate-500" />
          <p className="text-sm font-medium text-slate-300">
            {file ? file.name : "Drop a file or click to browse"}
          </p>
          <p className="mt-1 text-xs text-slate-500">CSV or TXT exports</p>
          <input
            type="file"
            accept=".csv,.txt,.tsv"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </label>

        {error && (
          <p className="mt-4 rounded-lg bg-red-500/10 px-4 py-2 text-sm text-red-400">
            {error}
          </p>
        )}
        {result && (
          <p className="mt-4 rounded-lg bg-breathe-500/10 px-4 py-2 text-sm text-breathe-300">
            {result}
          </p>
        )}

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            className="btn-primary"
            disabled={!file || loading}
            onClick={handleUpload}
          >
            {loading ? "Processing…" : "Upload & ingest"}
          </button>
        </div>
      </div>
    </div>
  );
}
