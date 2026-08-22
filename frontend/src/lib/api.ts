// In production (Vercel), the backend is reached through the same-origin
// "/api/*" rewrite in vercel.json, so the base URL should be empty (relative)
// unless NEXT_PUBLIC_API_URL explicitly overrides it. Local dev still targets
// the standalone uvicorn server on :8000 by default.
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000");

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers ?? {}),
  };
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Auth
export const auth = {
  googleLogin: () => request<{ auth_url: string }>("/api/auth/google/login", { method: "POST" }),
  me: () => request<User>("/api/auth/me"),
  logout: () => request("/api/auth/logout", { method: "POST" }),
};

// Emails
export const emails = {
  list: (params?: EmailFilter) => {
    const qs = new URLSearchParams(
      Object.entries(params ?? {}).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)])
    ).toString();
    return request<EmailListResponse>(`/api/emails${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => request<Email>(`/api/emails/${id}`),
  sync: () => request<{ synced: number; total_fetched: number }>("/api/emails/sync", { method: "POST" }),
  process: (id: string) =>
    request<{ classification: Classification; tasks_created: number }>(`/api/emails/process/${id}`, {
      method: "POST",
    }),
  updateStatus: (id: string, status: string) =>
    request(`/api/emails/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
};

// Tasks
export const tasks = {
  list: (params?: TaskFilter) => {
    const qs = new URLSearchParams(
      Object.entries(params ?? {}).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)])
    ).toString();
    return request<Task[]>(`/api/tasks${qs ? `?${qs}` : ""}`);
  },
  create: (data: TaskCreate) => request<Task>("/api/tasks", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Partial<TaskCreate & { completed: boolean }>) =>
    request<Task>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: string) => request(`/api/tasks/${id}`, { method: "DELETE" }),
};

// Briefings
export const briefings = {
  generate: () => request<Briefing>("/api/briefings/generate", { method: "POST" }),
  latest: () => request<Briefing>("/api/briefings/latest"),
};

// Job applications
export const jobApplications = {
  list: (params?: JobApplicationFilter) => {
    const qs = new URLSearchParams(
      Object.entries(params ?? {}).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)])
    ).toString();
    return request<JobApplication[]>(`/api/job-applications${qs ? `?${qs}` : ""}`);
  },
  create: (data: JobApplicationCreate) =>
    request<JobApplication>("/api/job-applications", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Partial<JobApplicationCreate>) =>
    request<JobApplication>(`/api/job-applications/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: string) => request(`/api/job-applications/${id}`, { method: "DELETE" }),
  scan: () => request<{ scanned: number; linked: number }>("/api/job-applications/scan", { method: "POST" }),
};

// Types
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface EmailListItem {
  id: string;
  gmail_message_id: string;
  sender_name: string | null;
  sender_email: string | null;
  subject: string | null;
  snippet: string | null;
  received_at: string | null;
  category: string;
  priority: string;
  status: string;
  processed: boolean;
}

export interface Email extends EmailListItem {
  body: string | null;
  thread_id: string | null;
  created_at: string;
}

export interface EmailListResponse {
  total: number;
  page: number;
  limit: number;
  items: EmailListItem[];
}

export interface EmailFilter {
  category?: string;
  priority?: string;
  status?: string;
  page?: number;
  limit?: number;
}

export interface Classification {
  category: string;
  priority: string;
  summary: string;
  action_required: boolean;
  confidence: number;
}

export interface Task {
  id: string;
  email_id: string | null;
  user_id: string;
  title: string;
  description: string | null;
  action_type: string;
  priority: string;
  deadline: string | null;
  completed: boolean;
  completed_at: string | null;
  created_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  action_type?: string;
  priority?: string;
  deadline?: string;
  email_id?: string;
}

export interface TaskFilter {
  completed?: boolean;
  priority?: string;
  action_type?: string;
}

export interface Briefing {
  id: string;
  user_id: string;
  briefing: string;
  generated_at: string;
}

export interface JobApplication {
  id: string;
  email_id: string | null;
  company_name: string;
  company_domain: string | null;
  role_title: string | null;
  status: string;
  source: "ai" | "manual";
  applied_at: string | null;
  last_contact_at: string | null;
  notes: string | null;
  awaiting_response: boolean;
  days_since_contact: number | null;
  created_at: string;
}

export interface JobApplicationCreate {
  company_name: string;
  role_title?: string;
  status?: string;
  applied_at?: string;
  notes?: string;
}

export interface JobApplicationFilter {
  status?: string;
  waiting_only?: boolean;
  search?: string;
  stale_days?: number;
}
