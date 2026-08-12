"use client";

import { SendIcon, Wand2Icon } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { PLATFORM_CONVERSIONS, type PlatformConversion } from "@/features/ai-chat/api/ai-chat-api";
import { useChatMessages, useConvertForPlatform, useRefineContent } from "@/features/ai-chat/api/use-ai-chat";
import { cn } from "@/lib/utils";

export function ChatThread({ contentId }: { contentId: string }) {
  const { data, isLoading } = useChatMessages(contentId);
  const refine = useRefineContent(contentId);
  const convert = useConvertForPlatform(contentId);
  const [instruction, setInstruction] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!instruction.trim() || refine.isPending) return;
    refine.mutate(instruction.trim(), { onSuccess: () => setInstruction("") });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Refine with AI</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {PLATFORM_CONVERSIONS.map((option) => (
            <Button
              key={option.value}
              variant="outline"
              size="sm"
              disabled={convert.isPending}
              onClick={() => convert.mutate(option.value as PlatformConversion)}
            >
              <Wand2Icon />
              {convert.isPending && convert.variables === option.value
                ? "Converting..."
                : `Convert to ${option.label}`}
            </Button>
          ))}
        </div>

        <div className="max-h-80 space-y-3 overflow-y-auto rounded-md border border-border p-3">
          {isLoading && <Skeleton className="h-16 w-full" />}
          {!isLoading && (!data || data.results.length === 0) && (
            <p className="text-sm text-muted-foreground">
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

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            placeholder="Ask for a change..."
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            disabled={refine.isPending}
          />
          <Button type="submit" disabled={refine.isPending || !instruction.trim()}>
            <SendIcon />
            {refine.isPending ? "Sending..." : "Send"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
