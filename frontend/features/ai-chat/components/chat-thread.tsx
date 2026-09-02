"use client";

import { SendIcon, Wand2Icon } from "lucide-react";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAIJob, useRetryAIJob } from "@/features/ai-jobs/api/use-ai-job";
import { PLATFORM_CONVERSIONS, type PlatformConversion } from "@/features/ai-chat/api/ai-chat-api";
import { useChatMessages, useConvertForPlatform, useRefineContent } from "@/features/ai-chat/api/use-ai-chat";
import { cn } from "@/lib/utils";

export function ChatThread({ contentId }: { contentId: string }) {
  const { data, isLoading } = useChatMessages(contentId);
  const refine = useRefineContent(contentId);
  const convert = useConvertForPlatform(contentId);
  const [instruction, setInstruction] = useState("");
  const [jobId, setJobId] = useState<string>();
  const { data: job } = useAIJob(jobId);
  const retryJob = useRetryAIJob();
  const queryClient = useQueryClient();
  const jobIsActive = job?.status === "queued" || job?.status === "running";
  const starters = ["Make this punchier", "Shorten this", "Add a stronger hook", "Make it more practical"];

  useEffect(() => {
    if (job?.status === "completed") {
      void queryClient.invalidateQueries({ queryKey: ["chat-messages", contentId] });
      void queryClient.invalidateQueries({ queryKey: ["generated-content", contentId] });
    }
  }, [contentId, job?.status, queryClient]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!instruction.trim() || refine.isPending || jobIsActive) return;
    refine.mutate(instruction.trim(), { onSuccess: (nextJob) => { setInstruction(""); setJobId(nextJob.id); } });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Refine with AI</CardTitle>
        <p className="text-sm text-muted-foreground">Refinement edits the current version in place. Generate again in Content Studio to keep a separate version.</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {PLATFORM_CONVERSIONS.map((option) => (
            <Button
              key={option.value}
              variant="outline"
              size="sm"
              disabled={convert.isPending || jobIsActive}
              onClick={() => convert.mutate(option.value as PlatformConversion, { onSuccess: (nextJob) => setJobId(nextJob.id) })}
            >
              <Wand2Icon />
              {convert.isPending || jobIsActive
                ? "Queueing..."
                : `Convert to ${option.label}`}
            </Button>
          ))}
        </div>

        {job && (
          <div className="rounded-md border border-border bg-muted/50 p-3 text-sm" role="status">
            {job.status === "queued" && "Your AI request is queued."}
            {job.status === "running" && "AI is applying your request…"}
            {job.status === "completed" && "Content updated."}
            {job.status === "failed" && (
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span>AI request failed: {job.error_message || "Please try again."}</span>
                {job.can_retry && <Button size="sm" variant="outline" onClick={() => retryJob.mutate(job.id, { onSuccess: (nextJob) => setJobId(nextJob.id) })}>Retry</Button>}
              </div>
            )}
          </div>
        )}

        <div className="max-h-80 space-y-3 overflow-y-auto rounded-md border border-border p-3">
          {isLoading && <Skeleton className="h-16 w-full" />}
          {!isLoading && (!data || data.results.length === 0) && (
            <p className="text-sm text-black/70 dark:text-white/70">
              No refinements yet. Ask for a change below, e.g. &quot;make it punchier&quot; or
              &quot;shorten to two lines&quot;.
            </p>
          )}
          {data?.results.map((message) => (
            <div
              key={message.id}
              className={cn(
                "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                message.role === "user"
                  ? "ml-auto bg-primary text-primary-foreground"
                  : "bg-muted text-foreground",
              )}
            >
              {message.message}
            </div>
          ))}
        </div>

        {refine.isError && (
          <p className="text-sm text-danger">
            Could not refine this content. Check that an AI provider key is configured.
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          {starters.map((starter) => <Button key={starter} size="sm" variant="outline" onClick={() => setInstruction(starter)} disabled={jobIsActive}>{starter}</Button>)}
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-2">
          <textarea
            placeholder="Ask for a change..."
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            disabled={refine.isPending || jobIsActive}
            rows={4}
            className="min-h-28 w-full resize-y rounded-md border border-input bg-background p-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
          />
          <Button type="submit" className="self-end" disabled={refine.isPending || jobIsActive || !instruction.trim()}>
            <SendIcon />
            {refine.isPending || jobIsActive ? "Queueing..." : "Send"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
