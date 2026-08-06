import { TrendList } from "@/features/trends/components/trend-list";

export default function TrendsPage() {
  return (
    <main className="flex flex-1 flex-col gap-6 p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Trends</h1>
        <p className="text-muted-foreground">
          Everything detected so far, across every connected source.
        </p>
      </div>
      <TrendList />
    </main>
  );
}
