# Databuddy HR — User Flows (MVP)

This document describes the **primary user flows** supported in the Databuddy HR MVP.  
Flows are written from the **user’s perspective**, with explicit system behavior at each step.

---

## Flow 1: Upload and Initial Validation

**Goal:** Upload an employee census file and understand whether it is valid.

### Steps
1. User selects a CSV or XLSX file and clicks **Upload**.
2. Frontend sends file to `POST /api/jobs`.
3. Backend:
   - Enforces single active job.
   - Validates file size (≤ 10 MB).
   - Parses file and validates row count (≤ 50,000).
   - Normalizes headers.
   - **Automatically drops unknown columns** (recorded as warnings).
   - Generates stable `row_id` for each row.
   - Writes original and working datasets to local disk.
   - Runs full validation against the fixed schema.
4. Frontend receives:
   - Validation summary (error/warning counts).
   - List of validation issues.
   - Dataset metadata (rows, canonical columns, dropped columns).

### User Outcomes
- If **errors exist**: user proceeds to fix them.
- If **no errors**: user may export immediately.

---

## Flow 2: Review Validation Issues

**Goal:** Understand what is wrong with the dataset.

### Steps
1. User views the validation summary panel.
2. User scans the list of issues:
   - Errors (blocking)
   - Warnings (non-blocking)
3. Structural issues (e.g., missing required columns) are clearly labeled.
4. Warnings about dropped unknown columns are visible but non-blocking.

### User Outcomes
- User identifies which rows/fields need correction.
- User decides whether warnings can be ignored.

---

## Flow 3: Browse Dataset (Paginated)

**Goal:** Inspect the dataset without loading it all at once.

### Steps
1. Frontend requests rows via `GET /api/jobs/{job_id}/rows?offset=&limit=`.
2. Backend returns:
   - Stable slice of rows in original file order.
   - Each row includes `row_id` and canonical columns only.
3. User pages forward/backward as needed.

### Notes
- No sorting or filtering in MVP.
- Pagination is offset/limit based.
- Unknown columns are never shown (already dropped).

---

## Flow 4: Fix a Single Cell Error

**Goal:** Correct a specific invalid value.

### Steps
1. User edits a cell in the grid (e.g., invalid email).
2. Frontend sends patch to `POST /api/jobs/{job_id}/edits`.
3. Backend:
   - Applies patch immediately to working dataset.
   - Runs full revalidation.
4. Frontend receives updated:
   - Validation summary.
   - Issue list.

### User Outcomes
- Error count decreases (or resolves).
- User continues fixing remaining issues.

---

## Flow 5: Apply a Bulk Fix

**Goal:** Fix many similar issues at once.

### Examples
- Trim whitespace from a column.
- Normalize casing.
- Replace a value globally.
- Map values to canonical enums.

### Steps
1. User selects a bulk action and configures parameters.
2. Frontend sends request to `POST /api/jobs/{job_id}/bulk`.
3. Backend:
   - Applies bulk transformation to working dataset.
   - Runs full revalidation.
4. Frontend updates validation state.

### User Outcomes
- Multiple issues resolved at once.
- User avoids repetitive manual edits.

---

## Flow 6: Reach “All Checks Passed”

**Goal:** Achieve a valid dataset ready for export.

### Steps
1. User continues editing and applying bulk actions.
2. Validation summary reaches:
   - `error_count = 0`
3. UI indicates **All checks passed**.

### Notes
- Warnings may still exist.
- Warnings do **not** block export.

---

## Flow 7: Export Corrected Dataset

**Goal:** Download a clean CSV for downstream import.

### Steps
1. User clicks **Export**.
2. Frontend calls `GET /api/jobs/{job_id}/export`.
3. Backend:
   - Confirms no blocking errors exist.
   - Generates CSV synchronously from working dataset.
4. Browser downloads the file.

### User Outcomes
- User receives a schema-compliant CSV.
- File is ready for HRIS / payroll import.

---

## Flow 8: Cleanup and Start Over

**Goal:** Clear current job and upload a new file.

### Steps
1. User clicks **Start new upload**.
2. Frontend calls `DELETE /api/jobs/{job_id}`.
3. Backend deletes local files and clears job state.
4. User is returned to upload screen.

---

## Error and Edge Flows

### Upload rejected
- File too large
- Too many rows
- Unsupported file type
- Missing required columns

**Result:** User receives immediate, actionable error message.

---

### Job already active
- User attempts to upload while a job exists.

**Result:** API returns 409 with instruction to delete current job first.

---

### Export blocked
- Errors still exist.

**Result:** Export fails with message indicating error count.

---

## MVP Constraints (User-Visible)

- One active job at a time
- No login or user accounts
- No persistence across refresh/server restart
- No row insertion/deletion
- No undo history

---

## Summary

These flows intentionally optimize for:
- Fast time-to-value
- Minimal cognitive overhead
- Clear, deterministic system behavior

They form a stable foundation for:
- Multi-user support
- Persistence
- Advanced workflows
- Integrations

without requiring rethinking the MVP UX or API model.