import { Sidebar } from "@/components/layout/sidebar";
import { Toaster } from "@/components/ui/toaster";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col lg:h-screen lg:flex-row lg:overflow-hidden">
      <Sidebar />
      <main className="flex-1 lg:overflow-y-auto bg-background p-4 sm:p-6">{children}</main>
      <Toaster />
    </div>
  );
}
