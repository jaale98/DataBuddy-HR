import type { Issue, JobState, RowsResponse } from "./types";

type ApiErrorPayload = {
  error: string;
  message: string;
  details?: Record<string, unknown>;
};

export class ApiError extends Error {
  status: number;
  details?: Record<string, unknown>;

  constructor(status: number, message: string, details?: Record<string, unknown>) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    let payload: ApiErrorPayload | null = null;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = null;
    }
    const message = payload?.message || `Request failed (${response.status})`;
    throw new ApiError(response.status, message, payload?.details);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function createJob(file: File): Promise<JobState> {
  const form = new FormData();
  form.append("file", file);
  return request<JobState>("/api/jobs", { method: "POST", body: form });
}

export async function getJob(jobId: string): Promise<JobState> {
  return request<JobState>(`/api/jobs/${jobId}`);
}

export async function getIssues(jobId: string): Promise<Issue[]> {
  return request<Issue[]>(`/api/jobs/${jobId}/issues`);
}

export async function getRows(
  jobId: string,
  offset: number,
  limit: number
): Promise<RowsResponse> {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  return request<RowsResponse>(`/api/jobs/${jobId}/rows?${params.toString()}`);
}

export async function applyEdit(
  jobId: string,
  rowId: string,
  column: string,
  value: string
): Promise<{ validation: JobState["validation"]; issues: Issue[] }> {
  return request(`/api/jobs/${jobId}/edits`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ edits: [{ row_id: rowId, column, value }] }),
  });
}

export async function applyBulkMap(
  jobId: string,
  column: string,
  defaultValue: string
): Promise<{ validation: JobState["validation"]; issues: Issue[] }> {
  return request(`/api/jobs/${jobId}/bulk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action_type: "map",
      column,
      params: { mapping: {}, default: defaultValue },
    }),
  });
}

export async function deleteJob(jobId: string): Promise<void> {
  await request<void>(`/api/jobs/${jobId}`, { method: "DELETE" });
}

export async function exportJob(jobId: string): Promise<Blob> {
  const response = await fetch(`/api/jobs/${jobId}/export`);
  if (!response.ok) {
    let payload: ApiErrorPayload | null = null;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = null;
    }
    const message = payload?.message || `Request failed (${response.status})`;
    throw new ApiError(response.status, message, payload?.details);
  }
  return await response.blob();
}
