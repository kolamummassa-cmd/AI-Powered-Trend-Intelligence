import { ContentPieceDetail } from "@/features/content-studio/components/content-piece-detail";

export default async function ContentPieceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="flex flex-1 flex-col gap-6 p-8">
      <ContentPieceDetail id={id} />
    </main>
  );
}
