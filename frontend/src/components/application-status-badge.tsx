import { Badge } from "@/components/ui/badge";

const variantMap: Record<string, "default" | "secondary" | "warning" | "destructive" | "critical" | "success" | "outline"> = {
  applied: "secondary",
  interviewing: "default",
  offer: "success",
  rejected: "destructive",
  withdrawn: "outline",
};

const labelMap: Record<string, string> = {
  applied: "Applied",
  interviewing: "Interviewing",
  offer: "Offer",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

export function ApplicationStatusBadge({ status }: { status: string }) {
  return <Badge variant={variantMap[status] ?? "outline"}>{labelMap[status] ?? status}</Badge>;
}
