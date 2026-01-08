# Databuddy HR — Data Model (MVP)

This document defines the **minimum data model** needed to keep the React frontend and FastAPI backend consistent for the MVP.

Scope notes:
- **No database** (no Postgres in MVP).
- All state is **ephemeral** and lasts only for the lifetime of the FastAPI process.
- **Single active job** at a time.
- Dataset is stored on **local disk** (`uploads/`, `working/`, `exports/`), while **job state and issues** are held in memory.

---

## 1) Core Entities

### 1.1 JobState (in-memory)

Represents the single active import session.

**Fields**
- `job_id: string` — server-generated identifier for the active job.
- `status: "uploaded" | "validating" | "ready" | "error"` — coarse lifecycle state.
- `created_at: string` — ISO 8601 timestamp.
- `schema_version: string` — fixed schema version label (e.g., `"v1"`).
- `limits: Limits` — enforced file size and row limits.
- `storage: StoragePaths` — absolute/relative paths to local disk artifacts.
- `dataset: DatasetMeta` — row/column counts and column lists.
- `validation: ValidationSummary` — counts and last validation timestamp.
- `issues: Issue[]` — current full set of issues (recomputed on every change).

**Notes**
- When the API process stops, `JobState` is lost and the local storage directory may be cleaned up.

---

### 1.2 StoragePaths

Pointers to local disk artifacts for the active job.

**Fields**
- `original_path: string` — e.g., `storage/uploads/original.csv` or `storage/uploads/original.xlsx`
- `working_path: string` — e.g., `storage/working/working.csv`
- `export_path: string | null` — e.g., `storage/exports/output.csv` (set after export)

---

### 1.3 Limits

Hard-enforced constraints.

**Fields**
- `max_rows: number` — **50_000**
- `max_bytes: number` — **10_000_000** (10 MB)

---

### 1.4 DatasetMeta

Metadata about the current working dataset.

**Fields**
- `total_rows: number`
- `total_columns: number`
- `canonical_columns: string[]` — normalized to your fixed schema names
- `unknown_columns: string[]` — columns not in schema that were automatically dropped during ingest (reported as warnings)
- `row_id_column: string` — always `"row_id"`

**Note**
- Unknown columns are never present in the working dataset.
- The working dataset contains only `row_id` and `canonical_columns`.

**Sorting guarantee**
- Rows are served in **original file order** (stable).
- No user-driven sorting in MVP.

---

## 2) Row Identity

### 2.1 row_id

A stable identifier generated on ingest and stored alongside the working dataset.

**Requirements**
- Generated once at ingest.
- Stable for the lifetime of the job.
- Unrelated to dataframe index (do not rely on index position for identity).
- Included in every row returned to the frontend.
- Used as the primary locator for edits and issues.

**Recommended strategy**
- `row_id = uuid4()` per row at ingest.

---

## 3) Validation Model

### 3.1 ValidationSummary

**Fields**
- `error_count: number`
- `warning_count: number`
- `last_validated_at: string` — ISO 8601 timestamp

---

### 3.2 Issue

Represents a single validation finding.

**Fields**
- `severity: "error" | "warning"`
- `type: string` — machine-readable identifier (e.g., `"missing_required"`, `"invalid_email"`)
- `row_id: string | null` — null for structural issues not tied to a row
- `column: string | null` — null if not column-specific
- `message: string` — user-facing description
- `suggestion: string | null` — optional remediation hint

**Uniqueness (recommended)**
To support stable UI rendering, the backend should produce issues that are stable across reruns:
- A deterministic `issue_key` can be derived as:
  - `issue_key = "{type}:{row_id or 'none'}:{column or 'none'}"`

This can remain computed (not necessarily stored) in MVP.

---

## 4) Edit and Bulk Action Models

### 4.1 EditPatch

Represents a single cell edit (patch-style).

**Fields**
- `row_id: string`
- `column: string`
- `value: string | number | boolean | null` — JSON-friendly value; backend coerces as needed

**Notes**
- Patches are **applied immediately** to `working.csv`.
- Backend runs **full revalidation** synchronously after applying edits.

---

### 4.2 BulkAction

Represents a column-wide or structural transformation.

**Base fields**
- `action_type: string`
- `column: string | null` — required for column-scoped actions
- `params: object` — action-specific configuration

**Supported `action_type` values (MVP)**
- `replace` — replace matching values
- `trim` — trim whitespace
- `case` — normalize casing
- `map` — map values by lookup table
- `rename_headers` — map uploaded headers to canonical schema headers

---

## 5) Pagination Model

### 5.1 PaginationRequest

**Fields**
- `offset: number` — starting row offset (0-based)
- `limit: number` — page size

**Constraints (recommended)**
- `limit` should be capped server-side (e.g., max 500 or 1000) to protect memory/latency.

---

### 5.2 PaginatedRowsResponse

**Fields**
- `offset: number`
- `limit: number`
- `total_rows: number`
- `rows: Row[]`

Where `Row` is a JSON object that always includes:
- `row_id: string`
- plus the canonical schema columns only (unknown columns are never returned)

---

## 6) API Payload Examples

### 6.1 `GET /api/jobs/{job_id}` (example response)

```json
{
  "job_id": "job_01HZZ...",
  "status": "ready",
  "created_at": "2026-01-06T04:10:12Z",
  "schema_version": "v1",
  "limits": { "max_rows": 50000, "max_bytes": 10000000 },
  "dataset": {
    "total_rows": 12842,
    "total_columns": 9,
    "canonical_columns": [
      "employee_id","first_name","last_name","date_of_birth","hire_date",
      "employment_status","job_title","work_email","department"
    ],
    "unknown_columns": [],
    "row_id_column": "row_id"
  },
  "validation": {
    "error_count": 12,
    "warning_count": 3,
    "last_validated_at": "2026-01-06T04:10:18Z"
  },
  "issues": [
    {
      "severity": "error",
      "type": "invalid_email",
      "row_id": "0b8a7cfe-7fd9-4a7a-8c3f-7b8f0dbb7e1e",
      "column": "work_email",
      "message": "Work email is not a valid email address.",
      "suggestion": "Enter an address like name@company.com."
    }
  ]
}
```

---

### 6.2 `GET /api/jobs/{job_id}/rows?offset=0&limit=2` (example response)

```json
{
  "offset": 0,
  "limit": 2,
  "total_rows": 12842,
  "rows": [
    {
      "row_id": "0b8a7cfe-7fd9-4a7a-8c3f-7b8f0dbb7e1e",
      "employee_id": "E10001",
      "first_name": "Ava",
      "last_name": "Nguyen",
      "date_of_birth": "1991-02-14",
      "hire_date": "2023-08-01",
      "employment_status": "active",
      "job_title": "Analyst",
      "work_email": "ava.nguyen@company.com",
      "department": "Finance"
    },
    {
      "row_id": "3c5c9f7b-8d8c-4e3a-a1d0-2d2c2a7d9c2b",
      "employee_id": "E10002",
      "first_name": "Noah",
      "last_name": "Patel",
      "date_of_birth": "1988-11-30",
      "hire_date": "2024-01-15",
      "employment_status": "active",
      "job_title": "Manager",
      "work_email": "noah.patel@company.com",
      "department": "Operations"
    }
  ]
}
```

---

### 6.3 `POST /api/jobs/{job_id}/edits` (example request)

```json
{
  "edits": [
    { "row_id": "0b8a7cfe-7fd9-4a7a-8c3f-7b8f0dbb7e1e", "column": "work_email", "value": "ava.nguyen@company.com" },
    { "row_id": "3c5c9f7b-8d8c-4e3a-a1d0-2d2c2a7d9c2b", "column": "employment_status", "value": "terminated" }
  ]
}
```

**Example response (shape)**
- Return updated `validation` + `issues` (and optionally updated summary metadata).

---

### 6.4 `POST /api/jobs/{job_id}/bulk` (example request)

Replace a value:

```json
{
  "action_type": "replace",
  "column": "department",
  "params": { "from": "HR", "to": "People Ops" }
}
```

Trim whitespace:

```json
{
  "action_type": "trim",
  "column": "work_email",
  "params": {}
}
```

Map values:

```json
{
  "action_type": "map",
  "column": "employment_status",
  "params": {
    "mapping": { "Active": "active", "Terminated": "terminated" },
    "default": null
  }
}
```

---

## 7) Enforced Single Active Job

Because MVP enforces **one job at a time**, requests must behave consistently:

- `POST /api/jobs`
  - If a job is active: return a clear error (e.g., HTTP 409 Conflict) with message:
    - `"An import job is already active. Delete the current job before uploading a new file."`

- All `{job_id}` endpoints
  - If `job_id` is not the active job: return 404.

---

## 8) Rejection Errors (Limits)

When limits are exceeded, reject immediately with a clear, structured error:

**Example**
```json
{
  "error": "upload_rejected",
  "reason": "file_too_large",
  "max_bytes": 10000000,
  "received_bytes": 14238711,
  "message": "Upload rejected: file exceeds the 10 MB limit."
}
```
