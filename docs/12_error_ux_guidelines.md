# Databuddy HR — Error & Warning UX Guidelines (MVP)

This document defines **how validation errors and warnings are presented to users**, including:
- messaging style
- severity distinctions
- grouping and ordering rules
- when issues block progress

The goal is to make errors **actionable, predictable, and low-friction**, even for non-technical users.

---

## 1) Core Principles

### 1.1 Errors are actionable
Every error message must clearly answer:
- What is wrong
- Where it is
- What the user should do next

Avoid technical jargon or schema-level language.

---

### 1.2 Errors block; warnings inform
- **Errors** must be resolved before export.
- **Warnings** never block export.

This distinction must be visually and verbally clear at all times.

---

### 1.3 Deterministic behavior
For the same dataset state:
- The same errors and warnings must appear
- In the same order
- With the same wording

This builds trust and avoids “why did this change?” confusion.

---

## 2) Severity Definitions

### 2.1 Error
An **error** indicates the dataset cannot be safely exported.

Examples:
- Missing required column
- Invalid email format
- Invalid enum value
- Duplicate employee ID
- Invalid date relationship (e.g., hire date before date of birth)

**User impact**
- Export is blocked
- Error count is prominently displayed
- Rows with errors are visually emphasized

---

### 2.2 Warning
A **warning** indicates a potential issue or automatic system action that does not block export.

Examples:
- Unknown columns automatically dropped
- Optional field missing
- Non-standard but acceptable formatting

**User impact**
- Export remains available
- Warning count is visible but de-emphasized
- Warnings are dismissible or ignorable

---

## 3) Message Style Guidelines

### 3.1 Tone
Messages should be:
- Clear
- Neutral
- Non-judgmental

Avoid:
- Blame (“You entered…”)
- Technical internals (“regex failed”)
- Vague language (“Something went wrong”)

---

### 3.2 Message structure

Preferred format:
[What is wrong]. [What needs to change].

Examples:
- ❌ “Invalid value.”
- ✅ “Work email is not a valid email address. Enter an address like name@company.com.”

---

### 3.3 Consistency
- Use the same phrasing everywhere a rule appears.
- Message text should come from a single source of truth (validation rules matrix).

---

## 4) Issue Grouping and Ordering

### 4.1 High-level grouping
Issues should be grouped in this order:
1. Structural errors (dataset-level)
2. Row-level errors
3. Cell-level errors
4. Warnings

This ensures users address blockers first.

---

### 4.2 Structural issues
Structural issues:
- Are not tied to a specific row
- Appear at the top of the issues list
- Cannot be resolved via cell editing

Examples:
- Missing required column
- File too large
- Dataset exceeds row limit

---

### 4.3 Row and cell issues
Row and cell issues:
- Reference a specific `row_id`
- Optionally reference a column
- Can be navigated to from the grid

Multiple issues in the same row should be visually grouped.

---

### 4.4 Warnings
Warnings appear:
- After all errors
- Collapsed by default if numerous
- With clear indication they do not block export

---

## 5) Error Counts and Status Indicators

### 5.1 Validation summary
The UI must always display:
- Total error count
- Total warning count

Example:
12 errors · 3 warnings

---

### 5.2 “All checks passed” state
When:
- error_count = 0

The UI should clearly indicate:
- “All checks passed”
- Export is available

Warnings may still be present and visible.

---

## 6) Navigation and Highlighting

### 6.1 Grid highlighting
Rows with errors:
- Are visually highlighted
- Remain highlighted until all errors in the row are resolved

Cells with errors:
- Are visually distinct from normal cells
- Display the error message on hover or focus

---

### 6.2 Issue-to-row navigation
Clicking an issue should:
- Navigate to the relevant row
- Bring the problematic cell into view if applicable

---

## 7) Automatic System Actions

### 7.1 Auto-dropped unknown columns
When unknown columns are dropped:
- A warning is generated
- The warning message should clearly state:
  - Which columns were dropped
  - That no user action is required

Example:
“The following columns were not recognized and were removed: Shirt Size, Nickname.”

---

### 7.2 Transparency
Automatic actions should never be silent.
Even non-blocking behavior must be communicated.

---

## 8) Error State Persistence

- Errors and warnings persist until:
  - The underlying data changes
  - The job is deleted
- Re-running validation without data changes must not reorder or alter issues.

---

## 9) Export Blocking UX

If export is attempted while errors exist:
- Export action is disabled **or**
- Export request fails with a clear message

Example:
“Export blocked. Resolve all errors before downloading.”

Do not allow partial exports in MVP.

---

## 10) What Is Explicitly Out of Scope (MVP)

- Inline auto-fixes
- AI-generated suggestions
- Undo/redo of edits
- Custom error suppression
- Per-user severity preferences

---

## Summary

The error UX for Databuddy HR prioritizes:
- Clear distinction between blocking and non-blocking issues
- Predictable, stable messaging
- Minimal user confusion during large data fixes

These guidelines ensure validation feels like **guided cleanup**, not punishment.
