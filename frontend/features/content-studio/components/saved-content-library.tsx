"use client";

import Link from "next/link";

import { ArrowRightIcon, BookmarkIcon, SparklesIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  CONTENT_TYPES,
  CONTENT_TYPE_DESCRIPTIONS,
  CONTENT_TYPE_LABELS,
} from "@/features/content-studio/api/content-studio-api";
import { useSavedContent } from "@/features/content-studio/api/use-content-studio";

export function SavedContentLibrary() {
  const { data, isLoading, isError } = useSavedContent();
  const visibleContent = data?.results.filter((content) =>
    CONTENT_TYPES.includes(content.content_type),
  );

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

  if (!visibleContent || visibleContent.length === 0) {
    return (
      <div className="rounded-2xl border border-primary/15 bg-linear-to-br from-primary/8 via-card to-warning/6 p-6 sm:p-10">
        <div className="mx-auto max-w-2xl text-center">
          <span className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <BookmarkIcon className="size-6" aria-hidden="true" />
          </span>
          <p className="mt-5 text-xs font-semibold uppercase tracking-[0.18em] text-primary">Build your library</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">Nothing saved yet</h2>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-muted-foreground">
            Turn a useful trend into a hook, short video script, or post, then save the version you want to keep.
          </p>
          <Button asChild className="mt-6">
            <Link href="/trends">
              Explore trends <ArrowRightIcon />
            </Link>
          </Button>
        </div>
        <div className="mx-auto mt-8 grid max-w-3xl gap-3 text-left sm:grid-cols-3">
          <LibraryStep number="01" title="Choose a trend" description="Open a signal that fits your audience." />
          <LibraryStep number="02" title="Generate content" description="Create the format you need in Content Studio." />
          <LibraryStep number="03" title="Save the best version" description="Return here whenever you are ready to publish." />
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {visibleContent.map((content) => (
        <Link
          key={content.id}
          href={`/content/${content.id}`}
          className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          aria-label={`Open ${CONTENT_TYPE_LABELS[content.content_type]} for ${content.trend_title}`}
        >
          <Card className="h-full cursor-pointer hover:-translate-y-0.5">
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="text-base">{CONTENT_TYPE_LABELS[content.content_type]}</CardTitle>
                <Badge variant="outline">v{content.version}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="mb-2 text-xs text-muted-foreground">{CONTENT_TYPE_DESCRIPTIONS[content.content_type]}</p>
              <p className="mb-2 text-sm font-medium text-foreground">{content.trend_title}</p>
              <p className="mb-2 text-xs text-muted-foreground">
                {content.perspective ? `${content.perspective.replaceAll("_", " ")} perspective` : "General perspective"}
              </p>
              <p className="line-clamp-4 whitespace-pre-wrap text-sm text-black/70 dark:text-white/70">
                {content.body}
              </p>
              <p className="mt-3 text-sm font-medium text-primary">Open item →</p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

function LibraryStep({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="rounded-xl border border-border/80 bg-background/70 p-4">
      <div className="flex items-center gap-2">
        <SparklesIcon className="size-4 text-primary" aria-hidden="true" />
        <span className="text-xs font-semibold tracking-[0.16em] text-primary">{number}</span>
      </div>
      <p className="mt-3 text-sm font-semibold">{title}</p>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">{description}</p>
    </div>
  );
}
