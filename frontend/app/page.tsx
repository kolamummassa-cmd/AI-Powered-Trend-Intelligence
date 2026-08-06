import { SystemStatusCard } from "@/features/system-health/components/system-status-card";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-8">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">
          AI-Powered Trend Intelligence
        </h1>
        <p className="mt-2 text-muted-foreground">
          Foundation phase — auth, trend engine, and content studio land next.
        </p>
      </div>
      <SystemStatusCard />
    </main>
  );
}
