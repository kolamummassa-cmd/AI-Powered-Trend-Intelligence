"use client";

import { Activity, AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useHealthCheck } from "@/features/system-health/api/use-health-check";

export function SystemStatusCard() {
  const { data, isLoading, isError } = useHealthCheck();

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="size-5 text-accent" />
          Platform Status
        </CardTitle>
        <CardDescription>
          Live connection between the frontend and the Django API.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex items-center gap-3">
            <Skeleton className="size-8 rounded-full" />
            <Skeleton className="h-4 w-40" />
          </div>
        )}

        {isError && (
          <div className="flex items-center gap-2 text-danger">
            <AlertTriangle className="size-5" />
            <span className="text-sm">Backend unreachable</span>
          </div>
        )}

        {data && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="size-5 text-success" />
              <span className="text-sm">API is healthy</span>
            </div>
            <Badge variant={data.database === "ok" ? "success" : "destructive"}>
              database: {data.database}
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
