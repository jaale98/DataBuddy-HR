export type DatasetMeta = {
  total_rows: number;
  total_columns: number;
  canonical_columns: string[];
  unknown_columns: string[];
  row_id_column: string;
};

export type ValidationSummary = {
  error_count: number;
  warning_count: number;
  last_validated_at: string;
};

export type Issue = {
  severity: "error" | "warning";
  type: string;
  row_id: string | null;
  column: string | null;
  message: string;
  suggestion: string | null;
};

export type JobState = {
  job_id: string;
  status: "uploaded" | "validating" | "ready" | "error";
  created_at: string;
  schema_version: string;
  limits: { max_rows: number; max_bytes: number };
  dataset: DatasetMeta | null;
  validation: ValidationSummary | null;
  issues: Issue[];
};

export type RowsResponse = {
  offset: number;
  limit: number;
  total_rows: number;
  total_filtered?: number;
  rows: Record<string, string | null>[];
};
