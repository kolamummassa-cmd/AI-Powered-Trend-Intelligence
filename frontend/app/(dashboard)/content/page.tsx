import { PageIntro } from "@/components/ui/page-intro";
import { SavedContentLibrary } from "@/features/content-studio/components/saved-content-library";

export default function ContentLibraryPage() {
  return (
    <main className="flex flex-1 flex-col gap-6 p-4 sm:p-8">
      <PageIntro
        eyebrow="Your content workspace"
        title="Content Library"
        description="Your saved publish-ready items. Open any card to copy, edit, or refine it."
      />
      <SavedContentLibrary />
    </main>
  );
}
