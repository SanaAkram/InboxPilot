"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PriorityBadge } from "@/components/priority-badge";
import { emails, tasks, type Email, type Task } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

const URL_PATTERN = /https?:\/\/[^\s]+/g;

/** Splits body text on raw URLs and renders them as truncated links, so long
 *  tracking URLs (no whitespace for the browser to wrap on) don't turn into
 *  an unreadable wall of text. */
function linkifyBody(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  URL_PATTERN.lastIndex = 0;
  while ((match = URL_PATTERN.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    const url = match[0];
    parts.push(
      <a
        key={key++}
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary underline underline-offset-2 hover:no-underline"
      >
        {url.length > 60 ? `${url.slice(0, 57)}…` : url}
      </a>
    );
    lastIndex = match.index + url.length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}

export default function EmailDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [email, setEmail] = useState<Email | null>(null);
  const [emailTasks, setEmailTasks] = useState<Task[]>([]);
  const [processing, setProcessing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [emailData, taskData] = await Promise.all([
          emails.get(id),
          tasks.list(),
        ]);
        setEmail(emailData);
        setEmailTasks(taskData.filter((t) => t.email_id === id));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  async function handleProcess() {
    setProcessing(true);
    try {
      const result = await emails.process(id);
      const [refreshedEmail, allTasks] = await Promise.all([emails.get(id), tasks.list()]);
      setEmail(refreshedEmail);
      setEmailTasks(allTasks.filter((t) => t.email_id === id));
      toast({
        title: "AI processing complete",
        description: `${result.tasks_created} task${result.tasks_created === 1 ? "" : "s"} created.`,
        variant: "success",
      });
    } catch (e: unknown) {
      toast({
        title: "Processing failed",
        description: (e as Error).message,
        variant: "destructive",
      });
    } finally {
      setProcessing(false);
    }
  }

  if (loading) return <div className="text-muted-foreground">Loading…</div>;
  if (!email) return <div className="text-muted-foreground">Email not found.</div>;

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-xl font-bold truncate">{email.subject || "(no subject)"}</h1>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-semibold">{email.sender_name || email.sender_email}</p>
              <p className="text-sm text-muted-foreground">{email.sender_email}</p>
              {email.received_at && (
                <p className="text-xs text-muted-foreground mt-1">
                  {new Date(email.received_at).toLocaleString()}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="capitalize">{email.category}</Badge>
              <PriorityBadge priority={email.priority} />
              <Badge variant={email.processed ? "success" : "secondary"}>
                {email.processed ? "Processed" : "Unprocessed"}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex justify-end mb-4">
            <Button onClick={handleProcess} disabled={processing} className="gap-2" size="sm">
              <Zap className="h-4 w-4" />
              {processing ? "Processing…" : "Run AI Processing"}
            </Button>
          </div>
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed bg-muted/30 rounded-lg p-4 border">
              {linkifyBody(email.body || email.snippet || "No content available.")}
            </pre>
          </div>
        </CardContent>
      </Card>

      {emailTasks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">AI-Extracted Tasks</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {emailTasks.map((task) => (
              <div key={task.id} className="flex items-center justify-between rounded-md border p-3">
                <div>
                  <p className={`font-medium ${task.completed ? "line-through text-muted-foreground" : ""}`}>
                    {task.title}
                  </p>
                  {task.deadline && (
                    <p className="text-xs text-muted-foreground">Due: {new Date(task.deadline).toLocaleDateString()}</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="capitalize text-xs">{task.action_type}</Badge>
                  <PriorityBadge priority={task.priority} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
