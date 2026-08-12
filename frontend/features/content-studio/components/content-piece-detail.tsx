"use client";

import { BookmarkIcon } from "lucide-react";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ChatThread } from "@/features/ai-chat/components/chat-thread";
import {
  CONTENT_TYPE_LABELS,
  setContentSaved,
} from "@/features/content-studio/api/content-studio-api";
import { useGeneratedContent } from "@/features/content-studio/api/use-content-studio";
import { cn } from "@/lib/utils";

export function ContentPieceDetail({ id }: { id: string }) {
  const { data: content, isLoading, isError } = useGeneratedContent(id);
  const queryClient = useQueryClient();

  const toggleSaved = useMutation({
    mutationFn: (isSaved: boolean) => setContentSaved(id, isSaved),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["generated-content", id] });
      queryClient.invalidateQueries({ queryKey: ["saved-content"] });
    },
  });

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
        <CardContent>
          <p className="whitespace-pre-wrap text-sm">{content.body}</p>
        </CardContent>
      </Card>

      <ChatThread contentId={content.id} />
    </div>
  );
}
