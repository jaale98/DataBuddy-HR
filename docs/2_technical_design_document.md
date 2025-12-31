# Databuddy HR — Technical Design Document (MVP)

## 1) Purpose
Databuddy HR is a **pre-ingestion data validation and correction tool** for HR employee census imports. It accepts **CSV/XLSX**, validates against a **fixed employee schema**, enables **interactive fixes (cell + column bulk actions)**, and outputs either:
- a **corrected export file**, or
- a **pass confirmation** when no errors remain.

No HRIS or database writeback is included in the MVP.

---

## 2) Users and Operating Model

**Primary users**
- HR Operations
- Benefits Operations
- Payroll administrators
- Implementation / onboarding specialists

**Primary workflow**
1. Upload file (CSV/XLSX)
2. System validates structure and content
3. User reviews and fixes errors in UI
4. User downloads corrected file or receives “all clear” confirmation

---

## 3) Input / Output Contracts

### Supported inputs
- `.csv` (UTF-8; delimiter handling fixed for MVP)
- `.xlsx` (first sheet only)

### Output
- `.csv` (canonical export format)

### File size constraints (MVP)
- Target: up to ~50k rows and ~25 columns
- In-memory processing with guardrails; streaming/chunking optional but not required

---

## 4) MVP Schema — Core Employee Census (Fixed)

### Required fields
- `employee_id` (string, non-null, unique)
- `first_name` (string, non-null)
- `last_name` (string, non-null)
- `date_of_birth` (date, valid, reasonable range)
- `hire_date` (date, valid, not in future)
- `employment_status` (enum: `active | terminated`)
- `job_title` (string, non-null)
- `work_email` (string, valid email)

### Optional fields
- `department` (string)

### Column handling rules
- Header matching is case-insensitive
- Canonical column names enforced on export
- Unknown columns flagged as warnings with option to drop

---

## 5) Validation Model

### Error classes

**Structural**
- Missing required column
- Duplicate headers
- Unsupported file type
- Empty file or no data rows

**Cell-level**
- Required field empty
- Invalid date format
- Invalid email format
- Enum value not in allowed set

**Row-level**
- Duplicate `employee_id`
- Invalid date logic (e.g., `hire_date` in the future)

### Validation output (conceptual)
Each issue includes:
- `severity`: `error` | `warning`
- `type`: machine-readable identifier
- `location`: row index + column (when applicable)
- `message`: user-facing description
- `suggestion`: optional remediation hint

---

## 6) Correction and Bulk Actions

### Cell-level edits
- Inline edit of a single cell
- Triggers re-validation of the affected cell and row

### Column-level bulk actions (MVP)
- Replace value (`"foo"` → `"bar"`)
- Normalize casing (upper / lower / title)
- Trim whitespace
- Map values via simple mapping table

### Structural actions
- Map uploaded headers to canonical schema headers
- Drop unknown columns

All transformations are applied to a working dataset and recorded internally as a transformation plan.

---

## 7) Architecture

### Frontend
- React (simple setup; Vite or equivalent)
- Minimal dependencies
- Key screens:
  1. Upload and schema matching
  2. Validation results with editable grid
  3. Export / success confirmation

### Backend
- Python with FastAPI
- Pandas for parsing and transformation
- Pydantic for schema definition and validation helpers

### Storage
- Ephemeral, job-based storage
- Each upload creates a `job_id`
- Data retained until TTL expiration or manual cleanup

### Data flow
1. Upload → parse → normalize headers → validate
2. User edits / bulk actions → targeted re-validation
3. Export corrected dataset

---

## 8) API Surface (MVP)

### Create job
`POST /api/jobs`
- Multipart file upload
- Returns `job_id`, schema status, validation summary, issues list

### Get job state
`GET /api/jobs/{job_id}`
- Returns dataset metadata and validation status

### Apply cell edits
`POST /api/jobs/{job_id}/edits`
- Payload: list of `{ row_id, column, value }`
- Returns updated validation state

### Apply bulk action
`POST /api/jobs/{job_id}/bulk`
- Payload: bulk action definition
- Returns updated validation state

### Export corrected data
`GET /api/jobs/{job_id}/export`
- Returns corrected CSV file

### Cleanup (optional)
`DELETE /api/jobs/{job_id}`

---

## 9) Key Data Structures

### Dataset representation
- Original (raw) dataframe
- Working dataframe with applied transformations
- Stable `row_id` independent of row index

### Validation index
- Issues keyed by `row_id`, `column`, and `type`
- Enables fast incremental updates on edits

---

## 10) Non-Functional Requirements

### Performance
- Initial validation completes within seconds for typical census sizes
- Incremental re-validation on edits where possible

### Security
- File size and type validation
- No long-term persistence of PII
- TLS assumed at deployment
- Authentication optional for MVP

### Reliability
- Deterministic validation and export behavior
- Clear failure messages for invalid inputs

### Observability
- Basic server logging for job lifecycle and validation timing

---

## 11) Out of Scope (MVP)
- HRIS or payroll integrations
- Database persistence
- Multi-tenant accounts or RBAC
- Custom schema builder
- AI-assisted suggestions
- Audit reports beyond corrected export

---

## 12) Suggested Repository Layout

/backend
app/main.py
app/schemas.py
app/validation/
app/transforms/
app/storage/

/frontend
src/pages/Upload.tsx
src/pages/ReviewFix.tsx
src/pages/Export.tsx
src/components/ErrorTable.tsx
src/components/EditGrid.tsx

---

## 13) MVP Acceptance Criteria
- Upload CSV/XLSX and detect missing required columns
- Validate against fixed schema with clear issue reporting
- Edit a single cell and see validation update
- Apply at least two bulk actions (replace, trim)
- Export corrected CSV with canonical headers
- Display “All checks passed” when no blocking issues remain