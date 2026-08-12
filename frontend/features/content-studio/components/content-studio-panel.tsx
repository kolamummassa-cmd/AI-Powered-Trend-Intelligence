"use client";

import { BookmarkIcon, RefreshCwIcon, SparklesIcon } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  CONTENT_TYPES,
  CONTENT_TYPE_LABELS,
  type ContentType,
  type GeneratedContent,
} from "@/features/content-studio/api/content-studio-api";
import {
  useBriefsForTrend,
  useCreateBrief,
  useCreateGeneratedContent,
  useSetContentSaved,
} from "@/features/content-studio/api/use-content-studio";
import { AUDIENCE_LABELS, AUDIENCE_TYPES, type AudienceType } from "@/features/trends/api/trends-api";
import { cn } from "@/lib/utils";

function latestByType(pieces: GeneratedContent[], contentType: ContentType) {
  return pieces
    .filter((piece) => piece.content_type === contentType)
    .sort((a, b) => b.version - a.version)[0];
}

// Matches components/ui/input.tsx's classes — no dedicated Select
// primitive exists in this project yet, and a plain native <select>
// styled the same way is the smallest addition that stays inside the
// existing design system rather than introducing a new component.
const SELECT_CLASSES =
  "h-11 rounded-lg border border-input bg-background px-4 py-2.5 text-sm " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:border-primary";

export function ContentStudioPanel({
  trendSlug,
  bestAudience,
}: {
  trendSlug: string;
  bestAudience?: AudienceType;
}) {
  const { data, isLoading } = useBriefsForTrend(trendSlug);
  const createBrief = useCreateBrief(trendSlug);
  const createContent = useCreateGeneratedContent(trendSlug);
  const setSaved = useSetContentSaved(trendSlug);

  const brief = data?.results[0];
  // CONTENT PERSPECTIVE: defaults to the trend's best audience purely
  // as a starting point — the user can always change it before
  // generating, and it never auto-updates to match best_audience once
  // touched. Independent of trend.best_audience from here on.
  const [perspective, setPerspective] = useState<AudienceType | "">(bestAudience ?? "");

  if (isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  const perspectiveSelector = (
    <div className="flex items-center gap-2">
      <label htmlFor="content-perspective" className="text-sm text-muted-foreground">
        Content Perspective
      </label>
      <select
        id="content-perspective"
        className={SELECT_CLASSES}
        value={perspective}
        onChange={(e) => setPerspective(e.target.value as AudienceType)}
      >
        {AUDIENCE_TYPES.map((audience) => (
          <option key={audience} value={audience}>
            {AUDIENCE_LABELS[audience]}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="text-base">Content Studio</CardTitle>
          {brief && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => createBrief.mutate(perspective)}
              disabled={createBrief.isPending}
            >
              <RefreshCwIcon />
              {createBrief.isPending ? "Regenerating brief..." : "Regenerate brief"}
            </Button>
          )}
        </div>
        {perspectiveSelector}
        <p className="text-xs text-muted-foreground">
          Controls the point of view used to generate the content angle, hooks, scripts, CTA,
          hashtags, and remix template below — independent of the trend&apos;s best audience.
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {!brief && (
          <div className="rounded-lg border border-dashed border-border py-10 text-center">
            <p className="mb-3 text-sm text-muted-foreground">
              No content brief yet — generate one to unlock hooks, scripts, hashtags, and more
              for this trend.
            </p>
            <Button onClick={() => createBrief.mutate(perspective)} disabled={createBrief.isPending}>
              <SparklesIcon />
              {createBrief.isPending ? "Generating brief..." : "Generate content brief"}
            </Button>
            {createBrief.isError && (
              <p className="mt-2 text-sm text-danger">
                Could not generate a brief. Check that an AI provider key is configured.
              </p>
            )}
          </div>
        )}

        {brief && (
          <>
            {brief.perspective && (
              <div className="space-y-1 rounded-md border border-border bg-muted/50 p-3">
                <div className="flex items-center gap-2">
                  <Badge variant="accent">{AUDIENCE_LABELS[brief.perspective]} perspective</Badge>
                </div>
                {brief.content_angle && (
                  <p className="text-sm text-muted-foreground">{brief.content_angle}</p>
                )}
              </div>
            )}

            <div className="grid gap-3 sm:grid-cols-2">
              <AngleBlurb label="Business angle" text={brief.business_angle} />
              <AngleBlurb label="Founder angle" text={brief.founder_angle} />
              <AngleBlurb label="Educational angle" text={brief.educational_angle} />
              <AngleBlurb label="Marketing angle" text={brief.marketing_angle} />
            </div>

            {brief.talking_points.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {brief.talking_points.map((point, i) => (
                  <Badge key={i} variant="outline" className="font-normal">
                    {point}
                  </Badge>
                ))}
              </div>
            )}

            <div className="space-y-3">
              {CONTENT_TYPES.map((contentType) => {
                const latest = latestByType(brief.generated_content, contentType);
                const isGenerating =
                  createContent.isPending && createContent.variables?.contentType === contentType;

                return (
                  <div key={contentType} className="rounded-md border border-border p-3">
                    <div className="mb-2 flex items-center justify-between gap-2">
                      <p className="text-sm font-medium">{CONTENT_TYPE_LABELS[contentType]}</p>
                      <div className="flex items-center gap-2">
                        {latest && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setSaved.mutate({
                                contentId: latest.id,
                                isSaved: !latest.is_saved,
                              })
                            }
                          >
                            <BookmarkIcon
                              className={cn(latest.is_saved && "fill-current text-primary")}
                            />
                            {latest.is_saved ? "Saved" : "Save"}
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            createContent.mutate({ briefId: brief.id, contentType })
                          }
                          disabled={isGenerating}
                        >
                          <RefreshCwIcon />
                          {isGenerating ? "Generating..." : latest ? "Regenerate" : "Generate"}
                        </Button>
                      </div>
                    </div>
                    {latest ? (
                      <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                        {latest.body}
                      </p>
                    ) : (
                      <p className="text-sm text-muted-foreground">Not generated yet.</p>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function AngleBlurb({ label, text }: { label: string; text: string }) {
  if (!text) return null;
  return (
    <div className="space-y-1">
      <p className="text-sm font-medium text-foreground">{label}</p>
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  );
}
