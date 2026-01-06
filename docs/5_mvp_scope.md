# Databuddy HR — MVP Scope

This document defines the **explicit scope** of the Databuddy HR Minimum Viable Product (MVP). It clarifies what the product **does**, what it **does not do**, and the boundaries that keep the MVP focused, opinionated, and buildable.

---

## Purpose of the MVP

The MVP exists to prove one core hypothesis:

> **HR data imports fail primarily due to preventable data quality issues that can be caught and fixed *before* upload.**

Databuddy HR’s MVP focuses exclusively on **pre-ingestion validation and correction** of employee census data.

---

## In-Scope Users (MVP)

The MVP is designed for:
- HR Operations / Benefits Administrators
- HRIS / Implementation / Operations Specialists
- Support / Ops teams (secondary users)

All users are assumed to be:
- Comfortable with spreadsheets
- Responsible for preparing or troubleshooting employee data imports
- Not engineers or database experts

---

## In-Scope Problems (MVP)

The MVP explicitly addresses:
- Failed imports caused by:
  - Missing required fields
  - Invalid values (dates, enums, emails)
  - Duplicate identifiers
  - Formatting and normalization issues
- Inefficient, trial-and-error spreadsheet debugging
- Lack of clear, actionable error feedback prior to upload

---

## Core Capabilities (What the MVP Does)

### 1. File Upload & Parsing
- Accepts:
  - CSV files
  - XLSX files (first sheet only)
- Validates:
  - File type
  - File is not empty
  - Headers are present

---

### 2. Fixed Employee Schema Validation
- Validates data against a **single, predefined employee schema**
- Enforces:
  - Required vs optional fields
  - Data types and formats
  - Allowed enum values
  - Basic cross-field logic (e.g. hire date not in the future)

> The schema is **not configurable** in the MVP.

---

### 3. Clear Error & Warning Reporting
- Flags issues at:
  - File level
  - Column level
  - Row / cell level
- Each issue includes:
  - Location (row + column)
  - Severity (error vs warning)
  - Human-readable explanation
  - Optional guidance for resolution

---

### 4. In-Tool Correction
- Users can:
  - Edit individual cells inline
  - Apply column-wide bulk actions, including:
    - Replace values
    - Normalize casing
    - Trim whitespace
- Validation re-runs after changes

---

### 5. Canonical Export
- Outputs a corrected CSV file with:
  - Canonical column headers
  - Normalized values
  - All blocking errors resolved
- Alternatively displays a clear **“All checks passed”** confirmation

---

## Explicit Non-Goals (Out of Scope for MVP)

The MVP **does not**:
- Import or write data into any HR, payroll, or benefits system
- Integrate with third-party platforms
- Support custom schemas or rule builders
- Persist employee data long-term
- Provide role-based access or multi-tenant accounts
- Offer AI-assisted fixes or recommendations
- Generate audit reports beyond the corrected export
- Automate downstream workflows

---

## Guardrails & Constraints

### Technical Constraints
- In-memory processing
- Reasonable file size limits (tens of thousands of rows)
- Deterministic, rule-based validation only

---

### Product Constraints
- Opinionated schema
- Minimal UI complexity
- Focus on clarity over flexibility
- Designed for speed and confidence, not completeness

---

## Success Criteria for MVP

The MVP is considered successful if:
- Users can move from upload → clean export in minutes
- The majority of common import errors are caught before upload
- Users understand and fix errors without external help
- Support and Ops see reduced escalation volume
- Users report the experience “feels like how imports should work”

---

## Why This Scope Is Intentionally Narrow

This MVP:
- Proves value without requiring integrations
- Avoids premature configurability
- Establishes a strong validation and correction foundation
- Creates a clear wedge for future expansion

Anything that does not directly support **pre-ingestion validation and correction** is intentionally deferred.

---