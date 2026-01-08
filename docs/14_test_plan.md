# Databuddy HR — Test Plan (MVP)

This test plan defines how to verify Databuddy HR MVP behavior. It is aligned to:
- the validation rules matrix (`9_validation_rules_matrix.xlsx`)
- the API contract (`10_api_contract.md`)
- user flows (`11_user_flows.md`)
- error UX guidelines (`12_error_ux_guidelines.md`)
- acceptance criteria (`13_acceptance_criteria.md`)

The plan intentionally includes both:
- **rule-level tests** (each validation rule)
- **edge case tests** (file format, parsing, limits, UX behaviors)

---

## 1) Test Strategy

### 1.1 Levels
- **Unit tests**
  - Header normalization/mapping
  - `row_id` generation
  - Validation rules (pure functions)
  - Bulk action transformations
- **Integration tests**
  - FastAPI endpoints with local disk storage
  - End-to-end flows: upload → validate → edit → revalidate → export
- **UI tests (optional MVP)**
  - Pagination behavior
  - Issues navigation
  - Export disabled/enabled states

### 1.2 Data sets
Maintain a small set of fixtures under a test directory (e.g., `tests/fixtures/`):
- `valid_minimal.csv`
- `valid_full.csv`
- `missing_required_column.csv`
- `invalid_email.csv`
- `duplicate_employee_id.csv`
- `unknown_columns.csv`
- `xlsx_valid.xlsx`
- `xlsx_empty_sheet.xlsx`
- `too_many_rows.csv` (generated)
- `too_large_file.csv` (generated)

### 1.3 Determinism requirement
All tests assume:
- same input yields same issues in same order
- warnings do not block export
- errors block export

---

## 2) Rule-Level Tests (Validation Rules Matrix)

> This section is written to map cleanly to your validation rule IDs.
> If your matrix IDs differ, update the `Rule ID` column references below to match.

### 2.1 Structural Rules

#### STR-001 Unsupported file type
- **Setup:** Upload a `.txt` file
- **Action:** `POST /api/jobs`
- **Expected:** `400` with `error=upload_rejected` (or `unsupported_file_type`)
- **UX:** Clear message listing allowed file types

#### STR-002 File too large (max bytes)
- **Setup:** Create file > 10 MB
- **Action:** `POST /api/jobs`
- **Expected:** `413`, `details.max_bytes=10000000`, `details.received_bytes>10000000`

#### STR-003 Too many rows (max rows)
- **Setup:** Generate CSV with 50,001+ data rows
- **Action:** `POST /api/jobs`
- **Expected:** `422` with `details.max_rows=50000`, `details.received_rows>50000`

#### STR-004 Empty file / no data rows
- **Setup:** CSV with header only, or XLSX with headers but no rows
- **Action:** `POST /api/jobs`
- **Expected:** `422` with clear message that dataset has no rows

#### STR-005 Duplicate headers (after normalization)
- **Setup:** CSV headers include `Email` and ` email ` (or equivalent duplicates)
- **Action:** `POST /api/jobs`
- **Expected:** `422` with message indicating duplicate header(s)

#### STR-006 Missing required column(s)
- **Setup:** Remove `employee_id` column
- **Action:** `POST /api/jobs`
- **Expected:** `422` with error listing missing columns

#### STR-007 Unknown columns auto-dropped (warning)
- **Setup:** Include extra column `nickname`
- **Action:** `POST /api/jobs`
- **Expected:** `201` with:
  - `dataset.unknown_columns` includes `nickname`
  - `issues` contains a warning describing dropped column(s)
- **Also verify:** `/rows` never includes `nickname`

---

### 2.2 Cell-Level Rules (per field)

> For each required field below, include both:
> - missing/blank test
> - type/format test (if applicable)

#### CELL-001 employee_id required
- **Setup:** row where employee_id is blank
- **Expected:** error issue with `column=employee_id`

#### CELL-002 first_name required
- **Setup:** blank `first_name`
- **Expected:** error issue with `column=first_name`

#### CELL-003 last_name required
- **Setup:** blank `last_name`
- **Expected:** error issue with `column=last_name`

#### CELL-004 date_of_birth required and valid date
- **Setup A:** blank DOB → error
- **Setup B:** invalid date string (`13/99/9999`) → error
- **Expected:** error issue with `column=date_of_birth`

#### CELL-005 hire_date required and valid date
- **Setup A:** blank hire_date → error
- **Setup B:** invalid date string → error
- **Expected:** error issue with `column=hire_date`

#### CELL-006 employment_status enum
- **Setup:** employment_status = `Active` (capital A) or `foo`
- **Expected:** error issue; suggestion includes allowed values (`active|terminated`)

#### CELL-007 job_title required
- **Setup:** blank job_title
- **Expected:** error issue

#### CELL-008 work_email valid email
- **Setup:** `work_email = "not-an-email"`
- **Expected:** error issue with suggestion

#### WARN-001 optional department missing
- **Setup:** blank department (if you treat as warning)
- **Expected:** warning issue (confirm if you actually emit this in MVP)

---

### 2.3 Row-Level Rules

#### ROW-001 employee_id uniqueness
- **Setup:** two rows share same employee_id
- **Expected:** error issues referencing both rows (or deterministic one-row reporting)

#### ROW-002 hire_date not in future
- **Setup:** hire_date > today
- **Expected:** error issue

#### ROW-003 date_of_birth reasonable range
- **Setup:** DOB too old (e.g., 1800-01-01) or DOB in future
- **Expected:** error issue (or warning if your matrix defines it so)

#### ROW-004 hire_date after date_of_birth
- **Setup:** hire_date earlier than DOB
- **Expected:** error issue referencing `hire_date` and/or both fields

---

## 3) Transformation Tests (Edits and Bulk Actions)

### 3.1 Apply cell edit updates working dataset
- **Setup:** upload `invalid_email.csv`
- **Action:** `POST /edits` to fix the email
- **Expected:**
  - returned `validation.error_count` decreases
  - subsequent `/rows` shows corrected value
  - export contains corrected value

### 3.2 Bulk: replace
- **Setup:** department contains `HR`
- **Action:** bulk replace `HR → People Ops`
- **Expected:** all affected rows updated, validation reruns, export matches

### 3.3 Bulk: trim
- **Setup:** emails with leading/trailing whitespace
- **Action:** trim work_email
- **Expected:** whitespace removed; invalid email errors may resolve

### 3.4 Bulk: case normalization
- **Setup:** last_name in inconsistent casing
- **Action:** case title
- **Expected:** casing updated; no schema break

### 3.5 Bulk: map
- **Setup:** employment_status has `Active/Terminated`
- **Action:** map to `active/terminated`
- **Expected:** enum errors resolved

### 3.6 Full revalidation always runs after mutations
- **Setup:** any dataset
- **Action:** edits and bulk
- **Expected:** `last_validated_at` changes and issues update deterministically

---

## 4) API Contract Tests

### 4.1 Job active conflict
- **Setup:** create job A
- **Action:** attempt `POST /api/jobs` again without deleting
- **Expected:** `409 job_active`

### 4.2 Wrong job_id returns 404
- **Setup:** active job exists with id A
- **Action:** call `/api/jobs/B`
- **Expected:** `404`

### 4.3 Pagination bounds
- **Setup:** dataset with N rows
- **Action:** `/rows?offset=N&limit=10`
- **Expected:** empty `rows` with `total_rows=N` (or 422 if you choose to reject)
- **Action:** negative offset or limit=0
- **Expected:** `422`

### 4.4 Limit clamping or rejection
- **Action:** request limit > 1000
- **Expected:** either:
  - clamped to 1000, or
  - `422` with message (pick one and test it)

### 4.5 Export blocked when errors exist
- **Setup:** dataset with errors
- **Action:** `GET /export`
- **Expected:** `409 export_blocked` with `details.error_count > 0`

### 4.6 Export succeeds when errors resolved
- **Setup:** fix errors
- **Action:** `GET /export`
- **Expected:** `200` CSV attachment; canonical headers only

### 4.7 Delete cleanup
- **Action:** `DELETE /api/jobs/{job_id}`
- **Expected:** `204`
- **Follow-up:** any subsequent job endpoints return `404`
- **Follow-up:** new upload allowed

---

## 5) UI/UX Behavior Tests (Guideline Alignment)

### 5.1 Error vs warning presentation
- **Setup:** dataset with both errors and warnings
- **Expected:**
  - error count and warning count visible
  - errors visually emphasized
  - warnings de-emphasized and do not block export UI

### 5.2 Grouping and ordering
- **Setup:** dataset triggers:
  - structural error
  - row error
  - cell error
  - warning
- **Expected:** displayed in order:
  1) structural
  2) row
  3) cell
  4) warnings

### 5.3 Issue-to-row navigation
- **Setup:** issue references row/cell visible in paginated grid
- **Action:** click issue
- **Expected:** grid navigates to page containing row and focuses cell

### 5.4 Deterministic messaging
- **Action:** refresh UI without changing data
- **Expected:** same messages and ordering

---

## 6) Edge Cases

### 6.1 CSV quoting and commas
- **Setup:** values containing commas inside quotes
- **Expected:** parser reads correctly; validation applies to interpreted values

### 6.2 Leading zeros in IDs
- **Setup:** employee_id like `000123`
- **Expected:** preserved as string, not coerced to int; export matches

### 6.3 Excel type coercion
- **Setup:** XLSX with numeric employee_id or date cells
- **Expected:** API converts to canonical string formats without losing meaning

### 6.4 Whitespace-only values
- **Setup:** field contains `"   "`
- **Expected:** treated as blank for required checks (if you adopt that rule)

### 6.5 Duplicate employee_id differing only by whitespace/case
- **Setup:** `E100` and ` e100 `
- **Expected:** choose and test normalization strategy:
  - either treated as duplicates, or distinct (recommended: trim; case-sensitive is optional)

### 6.6 Large warning lists
- **Setup:** many unknown columns (in a contrived file)
- **Expected:** warning message remains readable (may truncate list in UI but preserve in details)

### 6.7 Restart behavior (ephemeral)
- **Setup:** upload job and then restart API
- **Expected:** UI shows job lost; requires re-upload; endpoints return 404

---

## 7) Traceability Matrix (Recommended)

Maintain a simple trace table (can live in the test suite README) mapping:
- Validation Rule ID → test name(s) → fixture file

Example:
- `STR-007` → `test_unknown_columns_dropped_warning` → `unknown_columns.csv`

---

## 8) Exit Criteria (When MVP is “tested”)

MVP is considered test-complete when:
- All **structural rule tests** pass
- All **field validation tests** pass
- All **row-level rule tests** pass
- Edits and bulk actions reliably resolve issues and trigger revalidation
- Export is blocked only when errors exist
- Unknown columns are never present in rows or export
- Single active job behavior is enforced consistently
- Deterministic ordering and messaging are verified

---

## Appendix: Assumptions encoded in tests
- max_rows = 50,000
- max_bytes = 10,000,000
- employment_status allowed values: `active`, `terminated`
- XLSX: first sheet only
- export requires `error_count = 0`
