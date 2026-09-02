"use client";

import { BookmarkIcon, RefreshCwIcon, SparklesIcon, Trash2Icon } from "lucide-react";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAIJob, useRetryAIJob } from "@/features/ai-jobs/api/use-ai-job";
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
  useDeleteContentBrief,
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
  const createContent = useCreateGeneratedContent();
  const setSaved = useSetContentSaved(trendSlug);
  const deleteBrief = useDeleteContentBrief(trendSlug);
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState<string>();
  const { data: job } = useAIJob(jobId);
  const retryJob = useRetryAIJob();

  useEffect(() => {
    if (job?.status === "completed") {
      void queryClient.invalidateQueries({ queryKey: ["content-briefs", trendSlug] });
    }
  }, [job?.status, queryClient, trendSlug]);

  const brief = data?.results[0];
  const jobIsActive = job?.status === "queued" || job?.status === "running";
  const jobLabel = job?.job_type.replaceAll("_", " ");
  // CONTENT PERSPECTIVE: defaults to the trend's best audience purely
  // as a starting point — the user can always change it before
  // generating, and it never auto-updates to match best_audience once
  // touched. Independent of trend.best_audience from here on.
  const [perspective, setPerspective] = useState<AudienceType | "">(bestAudience ?? "");

  if (isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  const perspectiveSelector = (
    <div className="flex flex-col gap-2 sm:max-w-md">
      <label htmlFor="content-perspective" className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
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
    <Card className="h-full rounded-2xl shadow-sm transition-shadow hover:translate-y-0 hover:shadow-md">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-baseline gap-3">
            <CardTitle className="text-xl">Content Studio</CardTitle>
            <span className="text-xs font-medium tracking-[0.2em] text-muted-foreground">02</span>
          </div>
          {brief && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => createBrief.mutate(perspective, { onSuccess: (nextJob) => setJobId(nextJob.id) })}
                disabled={createBrief.isPending || jobIsActive}
              >
                <RefreshCwIcon />
                {createBrief.isPending || jobIsActive ? "Queueing brief..." : "Regenerate brief"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (window.confirm("Delete this brief and all of its generated content? This removes it from your library.")) {
                    deleteBrief.mutate(brief.id);
                  }
                }}
                disabled={deleteBrief.isPending}
              >
                <Trash2Icon />
                Delete brief
              </Button>
            </div>
          )}
        </div>
        {perspectiveSelector}
        <p className="text-xs leading-5 text-muted-foreground">
          Choose who this content is for. You can change the perspective before generating.
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {job && (
          <div className="rounded-md border border-border bg-muted/50 p-3 text-sm" role="status">
            {job.status === "queued" && `Your ${jobLabel} is queued.`}
            {job.status === "running" && `Generating ${jobLabel}…`}
            {job.status === "completed" && "Generation complete — your content has refreshed."}
            {job.status === "failed" && (
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span>Generation failed: {job.error_message || "Please try again."}</span>
                {job.can_retry && (
                  <Button size="sm" variant="outline" onClick={() => retryJob.mutate(job.id, { onSuccess: (nextJob) => setJobId(nextJob.id) })}>
                    Retry
                  </Button>
                )}
              </div>
            )}
          </div>
        )}
        {!brief && (
          <div className="space-y-5">
            <Button
              className="w-full"
              onClick={() => createBrief.mutate(perspective, { onSuccess: (nextJob) => setJobId(nextJob.id) })}
              disabled={createBrief.isPending || jobIsActive}
            >
              <SparklesIcon />
              {createBrief.isPending || jobIsActive ? "Queueing brief..." : "Generate content brief"}
            </Button>
            {createBrief.isError && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/35 bg-destructive/10 px-4 py-3 text-sm">
                <div>
                  <p className="font-medium text-foreground">Could not generate a brief.</p>
                  <p className="mt-1 text-muted-foreground">Check that an AI provider key with available credit is configured.</p>
                </div>
                <Button size="sm" variant="link" onClick={() => createBrief.mutate(perspective, { onSuccess: (nextJob) => setJobId(nextJob.id) })}>
                  Retry
                </Button>
              </div>
            )}
            <div className="border-t border-border pt-5">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">How it works</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                <WorkflowStep number="1" title="Collect the signal" description="The source feed is recorded and linked as evidence." />
                <WorkflowStep number="2" title="Assess the opportunity" description="Kuzana scores relevance, timing, and confidence." />
                <WorkflowStep number="3" title="Draft the brief" description="Generate a practical angle from your chosen perspective." />
              </div>
            </div>
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
                  (createContent.isPending && createContent.variables?.contentType === contentType) || jobIsActive;

                return (
                  <div key={contentType}>
                    {contentType === "script_60" && (
                      <p className="pt-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Advanced publishing assets
                      </p>
                    )}
                  <div className="rounded-md border border-border p-3">
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
                            createContent.mutate({ briefId: brief.id, contentType }, { onSuccess: (nextJob) => setJobId(nextJob.id) })
                          }
                          disabled={isGenerating}
                        >
                          <RefreshCwIcon />
                          {isGenerating ? "Queueing..." : latest ? "Regenerate" : "Generate"}
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

function WorkflowStep({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="grid grid-cols-[1.25rem_1fr] gap-x-2">
      <span className="text-sm font-semibold text-primary">{number}</span>
      <div>
        <p className="text-sm font-medium text-foreground">{title}</p>
        <p className="mt-1 text-xs leading-5 text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
