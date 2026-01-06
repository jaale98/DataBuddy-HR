# Databuddy HR — Jobs To Be Done by Persona

This document reframes the core Jobs To Be Done (JTBD) for **Databuddy HR** around the primary user personas. It clarifies *who* is hiring the product, *why*, and *what outcome* they expect, while staying aligned to the MVP scope.

---

## Primary Personas

### HR Operations / Benefits Administrator
Owns employee census data and is responsible for successful imports into HR, benefits, or payroll systems.

### HRIS / Implementation / Ops Specialist
Supports multiple clients or internal teams with onboarding and data imports, often under time pressure.

### Support / Operations (Secondary)
Diagnoses failed imports and data issues after the fact; measured on speed and volume, not data prep.

---

## Persona 1: HR Operations / Benefits Administrator

### JTBD-01 — Validate employee data before import
**When** I am preparing an employee census file for an upcoming import  
**I want to** validate the file against a known, correct schema  
**So that** I can avoid failed uploads and last-minute fixes.

---

### JTBD-02 — Understand exactly what is wrong
**When** my file contains errors  
**I want to** see clear explanations tied to specific rows and columns  
**So that** I know what to fix without technical help.

---

### JTBD-03 — Fix issues directly and quickly
**When** errors are identified  
**I want to** correct individual cells or entire columns in one place  
**So that** I don’t need to juggle spreadsheets and repeated uploads.

---

### JTBD-04 — Feel confident before uploading
**When** the tool shows no blocking issues  
**I want to** trust that the file is ready  
**So that** I can proceed without anxiety or second-guessing.

---

## Persona 2: HRIS / Implementation / Ops Specialist

### JTBD-05 — Standardize import readiness across many files
**When** I handle multiple census files across teams or clients  
**I want to** validate all files against the same rules  
**So that** data quality is predictable and consistent.

---

### JTBD-06 — Resolve errors at scale
**When** the same issue appears repeatedly  
**I want to** apply bulk corrections efficiently  
**So that** large datasets can be fixed in minutes, not hours.

---

### JTBD-07 — Reduce back-and-forth with stakeholders
**When** data issues are discovered  
**I want to** point to clear, system-generated validation results  
**So that** I can avoid subjective debates about “what’s wrong.”

---

### JTBD-08 — Deliver a clean, ready-to-use output
**When** validation is complete  
**I want to** export a standardized, corrected file  
**So that** downstream systems accept it on the first attempt.

---

## Persona 3: Support / Operations (Secondary)

### JTBD-09 — Catch problems earlier in the process
**When** customers or internal teams prepare files  
**I want to** prevent common errors before upload  
**So that** fewer failed imports reach support queues.

---

### JTBD-10 — Diagnose data issues faster
**When** something does go wrong  
**I want to** see structured, consistent error reporting  
**So that** I can quickly identify root causes without manual investigation.

---

## Emotional & Organizational Outcomes (Across Personas)

- Reduced stress around high-stakes imports  
- Fewer rework cycles and trial-and-error uploads  
- Clear ownership of data quality before ingestion  
- Less reliance on engineers or deep system knowledge  

---

## Explicit Non-Jobs (MVP)

Databuddy HR is **not** intended to:
- Import data into HR systems
- Replace HRIS, payroll, or benefits platforms
- Support custom schemas or rule builders
- Automate downstream workflows or integrations