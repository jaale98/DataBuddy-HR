# Databuddy HR — API Contract (MVP)

This document defines the **HTTP API contract** for Databuddy HR MVP.

## Scope and operating assumptions
- **Single active job** at a time (single user, no auth).
- **Ephemeral**: if the API process stops, job state and files are lost.
- Dataset stored on **local disk** (`uploads/`, `working/`, `exports/`).
- **Unknown columns are auto-dropped on ingest** and reported as warnings.
- **Full revalidation** occurs after upload, edits, and bulk actions.
- Hard limits (reject immediately):
  - `max_rows = 50,000`
  - `max_bytes = 10,000,000` (10 MB)

---

## 1) Conventions

### 1.1 Base URL
- All endpoints are prefixed with: `/api`
- Example: `POST /api/jobs`

### 1.2 Content types
- JSON requests/responses: `application/json`
- Upload: `multipart/form-data`
- Export download: `text/csv` (attachment)

### 1.3 Date/time formats
- Timestamps: ISO 8601 (UTC) (e.g., `2026-01-07T03:12:45Z`)
- Date fields in rows: `YYYY-MM-DD` strings (or `null`)

### 1.4 Row value typing (MVP)
Row values returned by the API are:
- **strings for display** (including dates in `YYYY-MM-DD` form)
- **null** for blanks
- Enums are strings (e.g., `"active"`, `"terminated"`)

Backend is responsible for coercion and canonical formatting on export.

### 1.5 Standard error format
All non-2xx responses should return:

```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "details": {}
}
```

`details` is optional and may be omitted or empty.

---

## 2) Core Models (Wire Shapes)

### 2.1 DatasetMeta
```json
{
  "total_rows": 12842,
  "total_columns": 9,
  "canonical_columns": ["employee_id","first_name","last_name","date_of_birth","hire_date","employment_status","job_title","work_email","department"],
  "unknown_columns": ["some_extra_col"],
  "row_id_column": "row_id"
}
```

Notes:
- `unknown_columns` lists **dropped** columns detected at ingest.
- Working dataset contains only `row_id` + `canonical_columns`.

### 2.2 ValidationSummary
```json
{
  "error_count": 12,
  "warning_count": 3,
  "last_validated_at": "2026-01-07T03:12:45Z"
}
```

### 2.3 Issue
```json
{
  "severity": "error",
  "type": "invalid_email",
  "row_id": "0b8a7cfe-7fd9-4a7a-8c3f-7b8f0dbb7e1e",
  "column": "work_email",
  "message": "Work email is not a valid email address.",
  "suggestion": "Enter an address like name@company.com."
}
```

Notes:
- `row_id` and `column` may be `null` for structural issues.

### 2.4 JobState (response shape)
```json
{
  "job_id": "job_01HZZ...",
  "status": "ready",
  "created_at": "2026-01-07T03:12:40Z",
  "schema_version": "v1",
  "limits": { "max_rows": 50000, "max_bytes": 10000000 },
  "dataset": { "...": "DatasetMeta" },
  "validation": { "...": "ValidationSummary" },
  "issues": [ { "...": "Issue" } ]
}
```

---

## 3) Endpoints

## 3.1 Create job (upload)
**`POST /api/jobs`**

Creates the single active job by uploading a CSV/XLSX file.

### Request
- Content-Type: `multipart/form-data`
- Form fields:
  - `file` (required): CSV or XLSX

### Success response
- Status: `201 Created`
- Body: `JobState`

### Error responses
- `400 Bad Request` — missing file, unsupported file type
- `409 Conflict` — job already active
- `413 Payload Too Large` — file exceeds `max_bytes`
- `422 Unprocessable Entity` — file parses but violates structural requirements (e.g., > max rows, empty, missing required columns)

### Example errors
Job active (409):
```json
{
  "error": "job_active",
  "message": "An import job is already active. Delete the current job before uploading a new file.",
  "details": {}
}
```

File too large (413):
```json
{
  "error": "upload_rejected",
  "message": "Upload rejected: file exceeds the 10 MB limit.",
  "details": {
    "reason": "file_too_large",
    "max_bytes": 10000000,
    "received_bytes": 14238711
  }
}
```

Too many rows (422):
```json
{
  "error": "upload_rejected",
  "message": "Upload rejected: dataset exceeds the 50,000 row limit.",
  "details": {
    "reason": "too_many_rows",
    "max_rows": 50000,
    "received_rows": 74211
  }
}
```

---

## 3.2 Get job state
**`GET /api/jobs/{job_id}`**

Returns current job metadata, validation summary, and issues.

### Success response
- Status: `200 OK`
- Body: `JobState`

### Error responses
- `404 Not Found` — no active job or job_id mismatch

---

## 3.3 Get paginated rows
**`GET /api/jobs/{job_id}/rows?offset={offset}&limit={limit}`**

Returns a page of rows from the working dataset.

### Query parameters
- `offset` (required, int >= 0)
- `limit` (required, int > 0)

Recommended server-side cap:
- If `limit` > 1000, server may clamp to 1000 (or reject with 422).

### Ordering guarantee (MVP)
- Rows are returned in **stable original file order**.
- No user-driven sorting supported.

### Success response
- Status: `200 OK`
- Body:
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
    }
  ]
}
```

### Error responses
- `404 Not Found` — no active job or job_id mismatch
- `422 Unprocessable Entity` — invalid offset/limit

---

## 3.4 Apply cell edits (patch-style)
**`POST /api/jobs/{job_id}/edits`**

Applies one or more cell edits to the working dataset and returns updated validation state.
- Edits are **applied immediately** to `working.csv`.
- Backend performs **full revalidation** synchronously.

### Request body
```json
{
  "edits": [
    { "row_id": "uuid", "column": "work_email", "value": "name@company.com" },
    { "row_id": "uuid", "column": "employment_status", "value": "terminated" }
  ]
}
```

### Success response
- Status: `200 OK`
- Body (minimal):
```json
{
  "validation": { "error_count": 10, "warning_count": 2, "last_validated_at": "2026-01-07T03:15:10Z" },
  "issues": [ { "...": "Issue" } ]
}
```

### Error responses
- `404 Not Found` — no active job or job_id mismatch
- `409 Conflict` — job busy (optional lock if another write/validate is in progress)
- `422 Unprocessable Entity` — invalid payload, unknown column, unknown row_id, or type coercion failure

Payload example (unknown column):
```json
{
  "error": "invalid_edit",
  "message": "Edit rejected: unknown column 'nickname'.",
  "details": { "column": "nickname" }
}
```

---

## 3.5 Apply bulk action
**`POST /api/jobs/{job_id}/bulk`**

Applies a bulk action (column-wide or structural) and returns updated validation state.
- Applied immediately to `working.csv`
- Full revalidation synchronously

### Supported actions (MVP)

#### replace
```json
{
  "action_type": "replace",
  "column": "department",
  "params": { "from": "HR", "to": "People Ops" }
}
```

#### trim
```json
{
  "action_type": "trim",
  "column": "work_email",
  "params": {}
}
```

#### case
```json
{
  "action_type": "case",
  "column": "last_name",
  "params": { "mode": "title" }
}
```

Allowed `mode`: `upper | lower | title`

#### map
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

#### rename_headers (ingest-time mapping)
This is primarily used during ingest; if exposed post-ingest, it should rewrite canonical headers.
```json
{
  "action_type": "rename_headers",
  "column": null,
  "params": {
    "mapping": { "Employee ID": "employee_id", "Email": "work_email" }
  }
}
```

### Success response
- Status: `200 OK`
- Body:
```json
{
  "validation": { "...": "ValidationSummary" },
  "issues": [ { "...": "Issue" } ]
}
```

### Error responses
- `404 Not Found` — no active job or job_id mismatch
- `409 Conflict` — job busy (optional)
- `422 Unprocessable Entity` — invalid action_type/params, unknown column

---

## 3.6 Export corrected CSV
**`GET /api/jobs/{job_id}/export`**

Generates and returns the corrected CSV from the current working dataset.
- Synchronous
- Blocks if there are **any errors** remaining (recommended)

### Success response
- Status: `200 OK`
- Headers:
  - `Content-Type: text/csv`
  - `Content-Disposition: attachment; filename="databuddy_export.csv"`
- Body: CSV bytes

### Error responses
- `404 Not Found` — no active job or job_id mismatch
- `409 Conflict` — blocking errors present (recommended)
- `500 Internal Server Error` — export failure

Blocking errors present (409):
```json
{
  "error": "export_blocked",
  "message": "Export blocked: resolve all errors before exporting.",
  "details": { "error_count": 5 }
}
```

---

## 3.7 Delete job (cleanup)
**`DELETE /api/jobs/{job_id}`**

Deletes local disk artifacts for the active job and clears in-memory job state.

### Success response
- Status: `204 No Content`

### Error responses
- `404 Not Found` — no active job or job_id mismatch

---

## 3.8 Health check (optional but recommended)
**`GET /api/health`**

### Success response
- Status: `200 OK`
```json
{ "status": "ok" }
```

---

## 4) Status codes summary
- `200 OK` — success
- `201 Created` — job created
- `204 No Content` — job deleted
- `400 Bad Request` — malformed request / missing file
- `404 Not Found` — job not found (no active job or wrong id)
- `409 Conflict` — job active, job busy, or export blocked
- `413 Payload Too Large` — file exceeds max bytes
- `422 Unprocessable Entity` — validation/constraint failure (rows limit, structural problems, bad params)
- `500 Internal Server Error` — unexpected failure

---

## 5) Notes for implementation alignment
- The API should be the single source of truth for:
  - header normalization
  - row_id generation
  - type coercion
  - validation + issue generation
- The frontend should treat `row_id` as opaque and stable.
- Unknown columns should never appear in `/rows` payloads; they are reported only via `dataset.unknown_columns` and warnings in `issues`.

```