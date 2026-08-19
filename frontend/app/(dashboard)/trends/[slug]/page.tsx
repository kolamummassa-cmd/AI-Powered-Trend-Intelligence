import { TrendDetail } from "@/features/trends/components/trend-detail";

export default async function TrendDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  return (
    <main className="flex flex-1 flex-col gap-6 p-4 sm:p-8">
      <TrendDetail slug={slug} />
    </main>
  );
}
