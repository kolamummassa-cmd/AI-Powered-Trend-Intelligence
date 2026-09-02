"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CONTENT_TYPE_LABELS } from "@/features/content-studio/api/content-studio-api";
import { useSavedContent } from "@/features/content-studio/api/use-content-studio";

export function SavedContentLibrary() {
  const { data, isLoading, isError } = useSavedContent();

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-40 w-full" />
        ))}
      </div>
    );
  }

  if (isError) {
    return <p className="text-sm text-danger">Could not load saved content.</p>;
  }

  if (!data || data.results.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border py-16 text-center">
        <p className="text-muted-foreground">
          Nothing saved yet. Save a hook, script, or hashtag set from a trend&apos;s Content
          Studio panel to see it here.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data.results.map((content) => (
        <Card key={content.id}>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="text-base">{CONTENT_TYPE_LABELS[content.content_type]}</CardTitle>
              <Badge variant="outline">v{content.version}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <p className="mb-2 text-sm font-medium text-foreground">{content.trend_title}</p>
            <p className="mb-2 text-xs text-muted-foreground">
              {content.perspective ? `${content.perspective.replaceAll("_", " ")} perspective` : "General perspective"}
            </p>
            {content.brief_context && <p className="mb-2 line-clamp-2 text-xs text-muted-foreground">Brief: {content.brief_context}</p>}
            <p className="line-clamp-4 whitespace-pre-wrap text-sm text-black/70 dark:text-white/70">
              {content.body}
            </p>
            <Link
              href={`/content/${content.id}`}
              className="mt-3 inline-block text-sm text-primary hover:underline"
            >
              Open
            </Link>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
