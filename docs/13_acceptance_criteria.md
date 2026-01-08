# Databuddy HR — Acceptance Criteria (MVP)

This document defines **acceptance criteria** for the Databuddy HR MVP.
Criteria are written to confirm that each core feature behaves correctly from a **user and system perspective**.

These criteria are intentionally explicit to support learning, implementation confidence, and future regression testing.

---

## 1) Upload & Parsing

### Feature: File Upload

**Acceptance Criteria**
- User can upload a `.csv` or `.xlsx` file.
- Upload is rejected if:
  - File size exceeds **10 MB**
  - Dataset exceeds **50,000 rows**
  - File type is unsupported
- Error messages clearly state:
  - Why the upload failed
  - The enforced limit (rows or bytes)

---

### Feature: XLSX Parsing

**Acceptance Criteria**
- Only the **first worksheet** is parsed.
- If the worksheet contains no data rows, upload is rejected with a clear error.
- Headers are read from the first row of the worksheet.

---

### Feature: Header Normalization

**Acceptance Criteria**
- Header matching is case-insensitive.
- Headers are trimmed of surrounding whitespace.
- Headers are mapped to canonical schema names where possible.
- Duplicate headers (after normalization) are rejected as errors.

---

### Feature: Unknown Columns Handling

**Acceptance Criteria**
- Columns not recognized by the schema are:
  - Automatically dropped during ingest
  - Reported as warnings
- Dropped columns:
  - Never appear in the preview grid
  - Never appear in exports
- Warning message lists the dropped column names.

---

## 2) Dataset Initialization

### Feature: Job Creation

**Acceptance Criteria**
- Only **one active job** may exist at a time.
- Attempting to upload while a job exists returns a conflict error.
- A successful upload returns:
  - Job metadata
  - Dataset metadata
  - Validation summary
  - Full list of validation issues

---

### Feature: Row Identity

**Acceptance Criteria**
- Each row is assigned a stable `row_id` at ingest.
- `row_id`:
  - Is unique per row
  - Does not change for the lifetime of the job
- All subsequent operations reference rows using `row_id`.

---

## 3) Validation

### Feature: Initial Validation

**Acceptance Criteria**
- Full validation runs immediately after upload.
- Validation rules are applied consistently across runs.
- Validation output includes:
  - Severity (`error` or `warning`)
  - Row and column references when applicable
  - Human-readable messages

---

### Feature: Validation Severity

**Acceptance Criteria**
- Errors:
  - Block export
  - Are clearly distinguished from warnings
- Warnings:
  - Never block export
  - Are visible but de-emphasized

---

### Feature: Deterministic Results

**Acceptance Criteria**
- Given the same dataset state:
  - Validation issues appear in the same order
  - Messages do not change
- Re-running validation without data changes does not modify issues.

---

## 4) Preview & Issues UI

### Feature: Dataset Preview

**Acceptance Criteria**
- Dataset preview:
  - Displays rows using offset/limit pagination
  - Preserves original file order
- Preview displays:
  - `row_id`
  - Canonical schema columns only

---

### Feature: Issues List

**Acceptance Criteria**
- Issues are grouped and ordered as:
  1. Structural errors
  2. Row-level errors
  3. Cell-level errors
  4. Warnings
- Issue counts are always visible.
- Clicking an issue navigates to the relevant row and cell.

---

### Feature: Visual Highlighting

**Acceptance Criteria**
- Rows containing errors are visually highlighted.
- Cells containing errors are visually distinct.
- Highlighting persists until errors are resolved.

---

## 5) Editing & Bulk Fixes

### Feature: Cell Editing

**Acceptance Criteria**
- User can edit individual cells in the preview grid.
- Edits are applied immediately to the working dataset.
- Full revalidation runs after edits.
- Validation summary updates in real time.

---

### Feature: Bulk Actions

**Acceptance Criteria**
- Supported bulk actions include:
  - Replace values
  - Trim whitespace
  - Normalize casing
  - Map values to canonical enums
- Bulk actions:
  - Apply to all applicable rows
  - Trigger full revalidation
  - Can resolve multiple issues at once

---

## 6) Export

### Feature: Export Availability

**Acceptance Criteria**
- Export is enabled only when:
  - `error_count = 0`
- Export remains enabled even if warnings exist.

---

### Feature: Export Output

**Acceptance Criteria**
- Export generates a CSV file synchronously.
- Exported file:
  - Contains canonical columns only
  - Uses canonical header names
  - Preserves corrected values
- Export file is suitable for downstream HR system import.

---

### Feature: Export Blocking

**Acceptance Criteria**
- If export is attempted with errors present:
  - Export is blocked
  - User receives a clear message explaining why

---

## 7) Import & Audit Logging (MVP Scope)

> Note: MVP does not persist logs beyond process lifetime. This section defines **behavioral expectations**, not long-term storage.

### Feature: Validation Activity Logging

**Acceptance Criteria**
- System logs:
  - Upload events
  - Validation runs
  - Export attempts
- Logs include timestamps and operation type.

---

### Feature: Error Transparency

**Acceptance Criteria**
- Automatic system actions (e.g., dropping unknown columns) are:
  - Logged internally
  - Communicated to the user via warnings

---

## 8) Cleanup & Reset

### Feature: Job Deletion

**Acceptance Criteria**
- User can delete the active job.
- Deleting a job:
  - Clears in-memory state
  - Removes local disk artifacts
- User is returned to the upload screen.

---

## 9) Failure & Edge Cases

### Feature: Process Restart

**Acceptance Criteria**
- If the API process stops:
  - All job state is lost
  - User must re-upload their file
- System behavior is documented and predictable.

---

## Summary

The MVP is accepted when:
- All core flows function as specified
- Validation behavior is deterministic and transparent
- Errors are actionable and clearly block export
- Warnings inform without obstructing progress
- Users can confidently produce a clean, import-ready CSV

These criteria define **what “done” means** for the Databuddy HR MVP.
