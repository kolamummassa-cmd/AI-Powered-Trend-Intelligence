"use client";

import { BookmarkIcon, CheckIcon, CopyIcon, DownloadIcon, PencilIcon, Trash2Icon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ChatThread } from "@/features/ai-chat/components/chat-thread";
import {
  CONTENT_TYPE_LABELS,
  deleteGeneratedContent,
  setContentSaved,
  updateContentBody,
} from "@/features/content-studio/api/content-studio-api";
import { useContentVersions, useGeneratedContent } from "@/features/content-studio/api/use-content-studio";
import { cn } from "@/lib/utils";

export function ContentPieceDetail({ id }: { id: string }) {
  const { data: content, isLoading, isError } = useGeneratedContent(id);
  const queryClient = useQueryClient();
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [copied, setCopied] = useState(false);

  const toggleSaved = useMutation({
    mutationFn: (isSaved: boolean) => setContentSaved(id, isSaved),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["generated-content", id] });
      queryClient.invalidateQueries({ queryKey: ["saved-content"] });
    },
  });
  const saveEdit = useMutation({
    mutationFn: (body: string) => updateContentBody(id, body),
    onSuccess: () => {
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ["generated-content", id] });
      queryClient.invalidateQueries({ queryKey: ["content-versions"] });
    },
  });
  const deleteContent = useMutation({
    mutationFn: () => deleteGeneratedContent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-content"] });
      queryClient.invalidateQueries({ queryKey: ["content-briefs"] });
      router.replace("/content");
    },
  });
  const { data: versions } = useContentVersions(content?.brief ?? "", content?.content_type ?? "hook");

  async function copyFor(format: string) {
    if (!content) return;
    const prefix = format === "Plain text" ? "" : `${format}\n\n`;
    await navigator.clipboard.writeText(`${prefix}${content.body}`);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  if (isLoading) return <Skeleton className="h-64 w-full" />;

  if (isError || !content) {
    return <p className="text-sm text-danger">Could not load this content piece.</p>;
  }

  return (
    <div className="space-y-4">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link href="/content">Back to content library</Link>
      </Button>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle>{CONTENT_TYPE_LABELS[content.content_type]}</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline">v{content.version}</Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={() => toggleSaved.mutate(!content.is_saved)}
                disabled={toggleSaved.isPending}
              >
                <BookmarkIcon className={cn(content.is_saved && "fill-current text-primary")} />
                {content.is_saved ? "Saved" : "Save"}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md bg-muted/50 p-3 text-sm text-muted-foreground">
            <p className="font-medium text-foreground">{content.trend_title}</p>
            <p className="mt-1">{content.perspective ? `${content.perspective.replaceAll("_", " ")} perspective` : "General perspective"}</p>
            {content.brief_context && <p className="mt-1">Brief: {content.brief_context}</p>}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={() => copyFor("Plain text")}><CopyIcon /> {copied ? "Copied" : "Copy"}</Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setDraft(content.body);
                setIsEditing((value) => !value);
              }}
            ><PencilIcon /> Edit</Button>
            <Button size="sm" variant="outline" onClick={() => copyFor("LinkedIn post")}><DownloadIcon /> LinkedIn</Button>
            <Button size="sm" variant="outline" onClick={() => copyFor("X post")}><DownloadIcon /> X</Button>
            <Button size="sm" variant="outline" onClick={() => copyFor("Reels / Shorts script")}><DownloadIcon /> Reels & Shorts</Button>
            <Button size="sm" variant="outline" onClick={() => copyFor("Carousel outline")}><DownloadIcon /> Carousel</Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                if (window.confirm("Delete this generated content? It will be removed from your library.")) {
                  deleteContent.mutate();
                }
              }}
              disabled={deleteContent.isPending}
            ><Trash2Icon /> Delete</Button>
          </div>
          {isEditing ? (
            <div className="space-y-2"><textarea value={draft} onChange={(event) => setDraft(event.target.value)} className="min-h-56 w-full rounded-md border border-input bg-background p-3 text-sm" /><div className="flex gap-2"><Button size="sm" onClick={() => saveEdit.mutate(draft)} disabled={saveEdit.isPending}><CheckIcon /> Save edits</Button><Button size="sm" variant="outline" onClick={() => { setDraft(content.body); setIsEditing(false); }}>Cancel</Button></div></div>
          ) : <p className="whitespace-pre-wrap text-sm">{content.body}</p>}
        </CardContent>
      </Card>

      {versions && versions.length > 1 && (
        <Card><CardHeader><CardTitle className="text-base">Version history</CardTitle></CardHeader><CardContent className="space-y-2">{versions.map((version) => <div key={version.id} className="flex items-center justify-between rounded-md border border-border p-3 text-sm"><span>Version {version.version}{version.id === content.id ? " · Current" : ""}</span>{version.id === content.id ? <Badge variant="accent">Open</Badge> : <Link href={`/content/${version.id}`} className="text-primary hover:underline">Compare</Link>}</div>)}</CardContent></Card>
      )}

      <ChatThread contentId={content.id} />
    </div>
  );
}
