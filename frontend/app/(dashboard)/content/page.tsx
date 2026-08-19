import { SavedContentLibrary } from "@/features/content-studio/components/saved-content-library";

export default function ContentLibraryPage() {
  return (
    <main className="flex flex-1 flex-col gap-6 p-4 sm:p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Content Library</h1>
        <p className="text-muted-foreground">Everything you&apos;ve saved from Content Studio.</p>
      </div>
      <SavedContentLibrary />
    </main>
  );
}
