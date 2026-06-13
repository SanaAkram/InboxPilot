import { Badge } from "@/components/ui/badge";

const variantMap: Record<string, "default" | "secondary" | "warning" | "destructive" | "critical" | "success" | "outline"> = {
  low: "secondary",
  medium: "default",
  high: "warning",
  critical: "critical",
};

export function PriorityBadge({ priority }: { priority: string }) {
  return <Badge variant={variantMap[priority] ?? "outline"}>{priority}</Badge>;
}
