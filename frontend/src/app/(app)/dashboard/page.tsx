"use client";

import { useEffect, useState } from "react";
import { Mail, CheckSquare, AlertTriangle, FileText, RefreshCw } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { emails, tasks, briefings, type EmailListResponse, type Task, type Briefing } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

interface Stats {
  totalEmails: number;
  pendingTasks: number;
  urgentEmails: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({ totalEmails: 0, pendingTasks: 0, urgentEmails: 0 });
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [generatingBriefing, setGeneratingBriefing] = useState(false);

  async function loadData() {
    const [emailData, taskData, briefingData] = await Promise.allSettled([
      emails.list({ limit: 1 }),
      tasks.list({ completed: false }),
      briefings.latest(),
    ]);

    if (emailData.status === "fulfilled") {
      const urgent = await emails.list({ priority: "critical", limit: 1 }).catch(() => ({ total: 0 }));
      setStats((s) => ({
        ...s,
        totalEmails: (emailData.value as EmailListResponse).total,
        urgentEmails: (urgent as EmailListResponse).total ?? 0,
      }));
    }
    if (taskData.status === "fulfilled") {
      setStats((s) => ({ ...s, pendingTasks: (taskData.value as Task[]).length }));
    }
    if (briefingData.status === "fulfilled") {
      setBriefing(briefingData.value as Briefing);
    }
  }

  useEffect(() => { loadData(); }, []);

  async function handleSync() {
    setSyncing(true);
    try {
      const res = await emails.sync();
      toast({
        title: "Sync complete",
        description: `${res.synced} new email${res.synced === 1 ? "" : "s"} synced.`,
        variant: "success",
      });
      await loadData();
    } catch (e: unknown) {
      toast({
        title: "Sync failed",
        description: (e as Error).message,
        variant: "destructive",
      });
    } finally {
      setSyncing(false);
    }
  }

  async function handleGenerateBriefing() {
    setGeneratingBriefing(true);
    try {
      const b = await briefings.generate();
      setBriefing(b);
      toast({ title: "Briefing ready", variant: "success" });
    } catch (e: unknown) {
      toast({
        title: "Failed to generate briefing",
        description: (e as Error).message,
        variant: "destructive",
      });
    } finally {
      setGeneratingBriefing(false);
    }
  }

  const statCards = [
    { label: "Total Emails", value: stats.totalEmails, icon: Mail, color: "text-blue-600" },
    { label: "Pending Tasks", value: stats.pendingTasks, icon: CheckSquare, color: "text-green-600" },
    { label: "Critical Emails", value: stats.urgentEmails, icon: AlertTriangle, color: "text-red-600" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Your AI-powered email command center</p>
        </div>
        <Button onClick={handleSync} disabled={syncing} variant="outline" className="gap-2">
          <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
          {syncing ? "Syncing…" : "Sync Gmail"}
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
              <Icon className={`h-5 w-5 ${color}`} />
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" /> Today&apos;s Briefing
            </CardTitle>
            <CardDescription>
              {briefing
                ? `Generated ${new Date(briefing.generated_at).toLocaleString()}`
                : "No briefing yet for today"}
            </CardDescription>
          </div>
          <Button onClick={handleGenerateBriefing} disabled={generatingBriefing} size="sm">
            {generatingBriefing ? "Generating…" : "Generate"}
          </Button>
        </CardHeader>
        <CardContent>
          {briefing ? (
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-foreground">
              {briefing.briefing}
            </pre>
          ) : (
            <p className="text-sm text-muted-foreground">
              Click &quot;Generate&quot; to create your AI-powered daily briefing.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
