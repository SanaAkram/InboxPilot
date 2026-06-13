"use client";

import { useEffect, useState } from "react";
import { Sparkles, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { briefings, type Briefing } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

export default function BriefingPage() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    briefings
      .latest()
      .then(setBriefing)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    try {
      const b = await briefings.generate();
      setBriefing(b);
      toast({ title: "Briefing ready", variant: "success" });
    } catch (e: unknown) {
      toast({
        title: "Generation failed",
        description: (e as Error).message,
        variant: "destructive",
      });
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Daily Briefing</h1>
          <p className="text-muted-foreground">AI-generated summary of your inbox and tasks</p>
        </div>
        <Button onClick={handleGenerate} disabled={generating} className="gap-2">
          {generating ? (
            <><RefreshCw className="h-4 w-4 animate-spin" /> Generating…</>
          ) : (
            <><Sparkles className="h-4 w-4" /> Generate</>
          )}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" /> Your Briefing
          </CardTitle>
          {briefing && (
            <CardDescription>
              Generated on {new Date(briefing.generated_at).toLocaleString()}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : briefing ? (
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
              {briefing.briefing}
            </pre>
          ) : (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <Sparkles className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No briefing generated yet. Click &quot;Generate&quot; to create your daily briefing.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
