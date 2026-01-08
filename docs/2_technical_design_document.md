# Databuddy HR — Technical Design Document (MVP)

## 1) Purpose

Databuddy HR is a **pre-ingestion data validation and correction tool** for HR employee census files.  
It accepts **CSV/XLSX uploads**, validates them against a **fixed employee schema**, allows **interactive cell and bulk corrections**, and produces either:

- a **corrected CSV export**, or  
- a **pass confirmation** when no blocking issues remain.

**No data is persisted beyond the lifetime of the API process.**  
If the service stops, all uploaded data and job state are discarded.

---

## 2) Users and Operating Model

### Primary users
- HR Operations
- Benefits Operations
- Payroll administrators
- Implementation / onboarding specialists

### Operating assumptions (MVP)
- Single active user at a time
- Single active import job at a time
- No authentication or authorization
- No resumability after process restart

---

## 3) Input / Output Contracts

### Supported inputs
- `.csv` (UTF-8)
- `.xlsx` (first worksheet only)

### Output
- `.csv` (canonical schema, normalized headers)

### File size and row limits (hard-enforced)
- **Maximum rows:** 50,000  
- **Maximum file size:** 10 MB  

Files exceeding either limit are **rejected immediately on upload** with a clear, user-facing error message.

Rationale:
- Fits comfortably in memory with Pandas
- Avoids UI and pagination performance degradation
- Keeps validation and export synchronous

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
- Unknown columns are automatically dropped during ingest and reported as warnings

---

## 5) Validation Model

### Validation scope
Validation runs **in full**:
- On initial upload
- After any cell edit
- After any bulk action

Incremental validation is explicitly **out of scope** for MVP.

### Error classes

**Structural**
- Missing required column
- Duplicate headers
- Unsupported file type
- Empty file / no data rows
- File exceeds size or row limits

**Cell-level**
- Required field empty
- Invalid date format
- Invalid email format
- Enum value not in allowed set

**Row-level**
- Duplicate `employee_id`
- Invalid date logic (e.g., hire date in the future)

### Validation output (conceptual)
Each issue includes:
- `severity`: `error | warning`
- `type`: machine-readable identifier
- `row_id`: stable row identifier
- `column`: optional
- `message`: user-facing explanation
- `suggestion`: optional remediation hint

---

## 6) Dataset and Identity Model

### Stable row identity
- A synthetic `row_id` is generated **on ingest**
- `row_id` is independent of dataframe index
- Used consistently for:
  - validation issues
  - pagination
  - edit and bulk action targeting

Row insertion and deletion are **out of scope** for MVP.

---

## 7) Corrections and Bulk Actions

### Cell-level edits
- Inline edit of a single cell
- Payload references `{ row_id, column, value }`
- Patch is **applied immediately** to the working dataset on disk
- Full revalidation runs synchronously

### Column-level bulk actions (MVP)
- Replace value (`"foo"` → `"bar"`)
- Normalize casing (upper / lower / title)
- Trim whitespace
- Map values via simple mapping table

### Structural actions
- Map uploaded headers to canonical schema headers

No transformation history is persisted beyond process memory.

---

## 8) Architecture (Conceptual)

### Frontend
- React (Vite or equivalent)
- Minimal dependencies
- Grid supports **offset/limit pagination**
- Sorting:
  - Stable by original file row order
  - No user-driven sorting in MVP

### Backend
- Python + FastAPI
- Pandas for parsing, transformation, and export
- Pydantic for schema definition and validation helpers

### Validation module
- Pure Python module
- No knowledge of:
  - file storage
  - API layer
  - job lifecycle
- Input: dataframe + schema rules
- Output: list of validation issues

### Storage (ephemeral)
- Local disk only
- Directory layout:
  /storage/
    /uploads/
      original.csv
    /working/
      working.csv
    /exports/
      output.csv

- Files deleted when:
- job is explicitly cleaned up, or
- API process stops

No database or external storage systems are used in MVP.

---

## 9) Data Flow

1. Upload file
2. Validate size and row limits
3. Parse into dataframe
4. Generate `row_id`
5. Normalize headers
6. Identify and drop unknown columns (recorded as warnings)
7. Run full validation
8. Persist working dataset to disk
9. User applies edits or bulk actions
10. Backend applies patches immediately
11. Full revalidation
12. Export generates CSV synchronously from working dataset

---

## 10) API Surface (MVP)

### Create job
`POST /api/jobs`
- Multipart file upload
- Rejects if another job is active
- Returns:
- job metadata
- validation summary
- issues list

### Get job state
`GET /api/jobs/{job_id}`
- Returns:
- pagination metadata
- validation summary
- current issues

### Get paginated rows
`GET /api/jobs/{job_id}/rows?offset=&limit=`
- Returns slice of working dataset
- Order is stable and deterministic

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
- Returns corrected CSV
- Synchronous

### Cleanup
`DELETE /api/jobs/{job_id}`
- Deletes all stored files
- Frees system for next upload

---

## 11) Non-Functional Requirements

### Performance
- Upload + initial validation completes in seconds for typical census sizes
- Pagination prevents full dataset transfer to browser

### Security
- Strict file type, size, and row validation
- No persistence of PII beyond process lifetime
- TLS assumed at deployment

### Reliability
- Deterministic validation and export behavior
- Clear, immediate errors on invalid inputs
- Single active job enforced with backend guard

### Observability
- Basic logging for:
- job lifecycle
- validation duration
- export timing

---

## 12) Out of Scope (MVP)

- Database persistence
- Multi-user support
- Authentication / RBAC
- Resumable jobs
- Incremental validation
- Row insertion/deletion
- Custom schema builder
- HRIS integrations
- AI-assisted fixes

---

## 13) MVP Acceptance Criteria

- Upload CSV/XLSX within size limits
- Reject oversized files with clear errors
- Validate against fixed schema
- Paginate dataset in UI
- Edit a cell and see validation update
- Apply bulk column action
- Export corrected CSV
- Confirm “All checks passed” state
- Enforce single active job at all times