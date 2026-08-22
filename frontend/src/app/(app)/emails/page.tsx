"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PriorityBadge } from "@/components/priority-badge";
import { emails, type EmailListItem, type EmailListResponse } from "@/lib/api";

const CATEGORIES = ["", "invoice", "meeting", "support", "urgent", "followup", "sales", "personal", "job_application", "other"];
const PRIORITIES = ["", "low", "medium", "high", "critical"];
const STATUSES = ["", "new", "reviewed", "archived"];

export default function EmailsPage() {
  const [data, setData] = useState<EmailListResponse | null>(null);
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const res = await emails.list({
        category: category || undefined,
        priority: priority || undefined,
        status: status || undefined,
        page,
        limit: 20,
      });
      setData(res);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [category, priority, status, page]);

  const totalPages = data ? Math.ceil(data.total / 20) : 1;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Emails</h1>
        <Button variant="outline" size="sm" onClick={load} className="gap-2">
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        {[
          { label: "Category", value: category, setValue: setCategory, options: CATEGORIES },
          { label: "Priority", value: priority, setValue: setPriority, options: PRIORITIES },
          { label: "Status", value: status, setValue: setStatus, options: STATUSES },
        ].map(({ label, value, setValue, options }) => (
          <select
            key={label}
            value={value}
            onChange={(e) => { setValue(e.target.value); setPage(1); }}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">{label}: All</option>
            {options.filter(Boolean).map((o) => (
              <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>
            ))}
          </select>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>
              {["Sender", "Subject", "Category", "Priority", "Status", "Received"].map((h) => (
                <th key={h} className="px-4 py-3 text-left font-medium text-muted-foreground">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">Loading…</td></tr>
            ) : data?.items.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">No emails found. Try syncing Gmail.</td></tr>
            ) : (
              data?.items.map((email: EmailListItem) => (
                <tr key={email.id} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium">{email.sender_name || "—"}</div>
                    <div className="text-xs text-muted-foreground">{email.sender_email}</div>
                  </td>
                  <td className="px-4 py-3 max-w-xs">
                    <Link href={`/emails/${email.id}`} className="font-medium hover:text-primary transition-colors">
                      {email.subject || "(no subject)"}
                    </Link>
                    {email.snippet && (
                      <p className="text-xs text-muted-foreground truncate max-w-[240px]">{email.snippet}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className="capitalize">{email.category}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={email.priority} />
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={email.status === "new" ? "default" : "secondary"} className="capitalize">
                      {email.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                    {email.received_at ? new Date(email.received_at).toLocaleDateString() : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.total > 20 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{data.total} total emails</span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span>Page {page} of {totalPages}</span>
            <Button variant="outline" size="icon" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
