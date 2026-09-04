import { SavedContentLibrary } from "@/features/content-studio/components/saved-content-library";

export default function ContentLibraryPage() {
  return (
    <main className="flex flex-1 flex-col gap-6 p-4 sm:p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Content Library</h1>
        <p className="text-black/70 dark:text-white/70">Your saved publish-ready items. Open any card to copy, edit, or refine it.</p>
      </div>
      <SavedContentLibrary />
    </main>
  );
}
