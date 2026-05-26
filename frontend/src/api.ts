const API_BASE = import.meta.env.VITE_API_URL || "/api";

function headers(): HeadersInit {
  const token = localStorage.getItem("token");
  return {
    ...(token ? { Authorization: `Token ${token}` } : {}),
  };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...headers(),
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
}

export interface DashboardStats {
  total_activities: number;
  pending_review: number;
  approved: number;
  rejected: number;
  locked: number;
  suspicious: number;
  failed_ingestions: number;
  by_source: Record<string, number>;
  by_scope: Record<string, number>;
  recent_runs: IngestionRun[];
}

export interface IngestionRun {
  id: number;
  source_type: string;
  filename: string;
  status: string;
  rows_total: number;
  rows_parsed: number;
  rows_failed: number;
  rows_suspicious: number;
  started_at: string;
}

export interface Activity {
  id: number;
  source_type: string;
  scope: string;
  category: string;
  activity_date: string | null;
  period_start?: string | null;
  period_end?: string | null;
  site_name: string;
  plant_code?: string;
  description: string;
  quantity: string | null;
  unit_original?: string;
  unit_normalized?: string;
  quantity_normalized?: string | null;
  amount: string | null;
  currency: string;
  origin?: string;
  destination?: string;
  distance_km?: string | null;
  is_suspicious: boolean;
  suspicion_reasons: string[];
  parse_warnings?: string[];
  review_status: string;
  review_notes?: string;
  source_reference?: string;
  ingestion_run_id?: number;
  audit_logs?: AuditLog[];
  created_at: string;
}

export interface AuditLog {
  id: number;
  action: string;
  performed_by_name: string;
  field_changes: Record<string, unknown>;
  note: string;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const api = {
  login: (username: string, password: string) =>
    request<{ token: string; user: User; organization: Organization }>(
      "/auth/login/",
      { method: "POST", body: JSON.stringify({ username, password }) }
    ),

  me: () =>
    request<{ user: User; organization: Organization }>("/auth/me/"),

  dashboard: () => request<DashboardStats>("/dashboard/"),

  activities: (params: Record<string, string> = {}) => {
    const q = new URLSearchParams(params).toString();
    return request<Paginated<Activity>>(`/activities/?${q}`);
  },

  activity: (id: number) => request<Activity>(`/activities/${id}/`),

  review: (id: number, action: string, notes = "") =>
    request<Activity>(`/activities/${id}/review/`, {
      method: "POST",
      body: JSON.stringify({ action, notes }),
    }),

  bulkReview: (ids: number[], action: string, notes = "") =>
    request<{ updated: number }>("/activities/bulk_review/", {
      method: "POST",
      body: JSON.stringify({ ids, action, notes }),
    }),

  upload: (sourceType: string, file: File) => {
    const form = new FormData();
    form.append("source_type", sourceType);
    form.append("file", file);
    return request<IngestionRun>("/upload/", { method: "POST", body: form });
  },

  runs: () => request<Paginated<IngestionRun>>("/runs/"),
};
