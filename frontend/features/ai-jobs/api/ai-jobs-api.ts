import { apiClient } from "@/lib/api/client";

export type AIJobStatus = "queued" | "running" | "completed" | "failed";

export interface AIJob {
  id: string;
  job_type: string;
  status: AIJobStatus;
  result: Record<string, string>;
  error_message: string;
  attempt_count: number;
  can_retry: boolean;
  created_at: string;
  updated_at: string;
}

export async function fetchAIJob(jobId: string) {
  const { data } = await apiClient.get<AIJob>(`/jobs/${jobId}/`);
  return data;
}

export async function retryAIJob(jobId: string) {
  const { data } = await apiClient.post<AIJob>(`/jobs/${jobId}/retry/`);
  return data;
}
