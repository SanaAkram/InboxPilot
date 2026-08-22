"use client";

import { useEffect, useState } from "react";
import { Plus, RefreshCw, Sparkles, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ApplicationStatusBadge } from "@/components/application-status-badge";
import { jobApplications, type JobApplication, type JobApplicationFilter } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

const STATUS_OPTIONS = ["applied", "interviewing", "offer", "rejected", "withdrawn"];

const FILTERS: { label: string; params: JobApplicationFilter }[] = [
  { label: "All", params: {} },
  { label: "Awaiting response", params: { waiting_only: true } },
  { label: "Interviewing", params: { status: "interviewing" } },
  { label: "Offer", params: { status: "offer" } },
  { label: "Rejected", params: { status: "rejected" } },
];

export default function ApplicationsPage() {
  const [apps, setApps] = useState<JobApplication[]>([]);
  const [filterIndex, setFilterIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await jobApplications.list(FILTERS[filterIndex].params);
      setApps(data);
    } catch {
      toast({ title: "Failed to load applications", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterIndex]);

  async function handleScan() {
    setScanning(true);
    try {
      const result = await jobApplications.scan();
      toast({ title: `Scanned ${result.scanned} email(s), linked ${result.linked}`, variant: "success" });
      await load();
    } catch {
      toast({ title: "Scan failed", variant: "destructive" });
    } finally {
      setScanning(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!companyName.trim()) return;
    setCreating(true);
    try {
      await jobApplications.create({
        company_name: companyName.trim(),
        role_title: roleTitle.trim() || undefined,
      });
      setCompanyName("");
      setRoleTitle("");
      toast({ title: "Application added", variant: "success" });
      await load();
    } catch {
      toast({ title: "Failed to add application", variant: "destructive" });
    } finally {
      setCreating(false);
    }
  }

  async function handleStatusChange(id: string, status: string) {
    await jobApplications.update(id, { status });
    toast({ title: "Status updated", variant: "success" });
    await load();
  }

  async function handleDelete(id: string) {
    await jobApplications.delete(id);
    toast({ title: "Application removed", variant: "default" });
    await load();
  }

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Applications</h1>
        <Button variant="outline" onClick={handleScan} disabled={scanning} className="gap-2">
          <RefreshCw className={`h-4 w-4 ${scanning ? "animate-spin" : ""}`} />
          Scan inbox
        </Button>
      </div>

      <div className="flex flex-wrap gap-1 rounded-lg border p-1 w-fit">
        {FILTERS.map((f, i) => (
          <button
            key={f.label}
            onClick={() => setFilterIndex(i)}
            className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
              filterIndex === i
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Quick add */}
      <form onSubmit={handleCreate} className="flex flex-wrap gap-2">
        <input
          type="text"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          placeholder="Company name…"
          className="flex-1 min-w-[160px] rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <input
          type="text"
          value={roleTitle}
          onChange={(e) => setRoleTitle(e.target.value)}
          placeholder="Role (optional)"
          className="flex-1 min-w-[160px] rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <Button type="submit" disabled={creating || !companyName.trim()} className="gap-2">
          <Plus className="h-4 w-4" /> Add
        </Button>
      </form>

      {/* List */}
      <div className="space-y-2">
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : apps.length === 0 ? (
          <p className="text-sm text-muted-foreground">No applications found.</p>
        ) : (
          apps.map((app) => (
            <div key={app.id} className="rounded-lg border bg-card p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-medium">{app.company_name}</p>
                    {app.source === "ai" && (
                      <span title="Auto-detected from your inbox">
                        <Sparkles className="h-3.5 w-3.5 text-muted-foreground" />
                      </span>
                    )}
                  </div>
                  {app.role_title && (
                    <p className="text-sm text-muted-foreground">{app.role_title}</p>
                  )}
                </div>

                <div className="flex shrink-0 items-center gap-2">
                  <ApplicationStatusBadge status={app.status} />
                  {app.awaiting_response && (
                    <Badge variant="warning">
                      No response{app.days_since_contact != null ? ` · ${app.days_since_contact}d` : ""}
                    </Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    onClick={() => handleDelete(app.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                <div className="flex flex-wrap gap-3">
                  {app.applied_at && <span>Applied {new Date(app.applied_at).toLocaleDateString()}</span>}
                  {app.last_contact_at && (
                    <span>Last contact {new Date(app.last_contact_at).toLocaleDateString()}</span>
                  )}
                </div>
                <select
                  value={app.status}
                  onChange={(e) => handleStatusChange(app.id, e.target.value)}
                  className="rounded-md border border-input bg-background px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s[0].toUpperCase() + s.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
