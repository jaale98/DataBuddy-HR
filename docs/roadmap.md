# End-to-end Roadmap: DataBuddy HR

This roadmap defines the recommended sequencing for delivery of DataBuddy HR. It is structured to reduce build-first churn while maintaining momentum toward an early working vertical slice. The roadmap emphasizes **product management artifacts + technical literacy**, with clear deliverables produced at each phase.

---

## Phase 0 — Project Setup (pre-discovery)

**Goal:** Establish structure so all future artifacts, decisions, and work items have a consistent home.

### Step 0.1 — Documentation skeleton

**Scope**
- `/docs` folder hierarchy (per agreed structure)
- `/docs/INDEX.md`
- `/docs/decisions/ADR-0001-template.md`

**Tools**
- VS Code
- Markdown
- GitHub

**Output**
- Repository documentation structure in place
- `/docs/INDEX.md` serves as the navigation hub

---

### Step 0.2 — Working backlog board

**Scope**
- GitHub Projects board with columns:
  - Inbox
  - Next
  - In Progress
  - Review
  - Done

**Tools**
- GitHub Projects
- GitHub Issues

**Output**
- Centralized backlog and workflow for capturing and tracking all work items

---

### Step 0.3 — Lightweight templates

**Scope**
- `.github/ISSUE_TEMPLATE/feature.md`
- `.github/ISSUE_TEMPLATE/bug.md`
- `.github/pull_request_template.md`

**Tools**
- GitHub
- Markdown

**Why this matters**
Standardization of intake and review reduces operational overhead and prevents project drift as work scales.

---

## Phase 1 — Framing + Discovery (PM work)

**Goal:** Define what is being built and why, prior to detailed specification.

### Step 1.1 — One-pager (1 page max)

**File**
- `/docs/product/01-one-pager.md`

**Contents**
- Problem
- Who it’s for
- What it does (MVP)
- What it doesn’t do
- Success metrics (draft)
- Risks/unknowns

**Tools**
- Markdown
- (Optional) Chat for first draft polish

**Output**
- A “north star” framing document referenced throughout the project

---

### Step 1.2 — Personas + JTBD

**File**
- `/docs/product/02-personas-jtbd.md`

**Contents**
- Persona 1: HR Admin
- Persona 2: HRIS/Ops Specialist
- JTBD statement for each

**Tools**
- Markdown
- Excalidraw or Figma (optional)

**Output**
- Shared user framing to support prioritization and UX decisions

---

### Step 1.3 — Current-state workflow + pain map

**File**
- `/docs/research/03-current-state-workflow.md`

**Scope**
Current workflow documentation:
- receives census file
- uploads
- gets errors
- re-exports
- resubmits
- escalates to support

Followed by:
- failure points
- cost of failure

**Tools**
- Mermaid flowchart in Markdown
- Real-world HR domain experience

**Output**
- Current-state workflow and a clear definition of what “better” means

---

## Phase 2 — Competitive Scan (tight, not academic)

**Goal:** Establish reference patterns and differentiation without over-investing in research.

### Step 2.1 — Competitive notes (1–2 pages)

**File**
- `/docs/research/04-competitive-scan.md`

**Coverage categories**
- Big HRIS imports (Workday/UKG-style)
- Payroll/benefits admin uploads
- “CSV template only” tools

**Focus**
- error UX quality
- how they guide fixes
- what they don’t validate until too late

**Tools**
- Markdown
- Screenshots (optional—use sparingly)

**Output**
- Competitive context supporting positioning and UX principles

---

## Phase 3 — MVP Scope + Success Metrics (lock boundaries)

**Goal:** Prevent scope creep and define measurable success.

### Step 3.1 — Scope doc + release definition

**File**
- `/docs/product/05-mvp-scope.md`

**Sections**
- MVP: must-have
- Not-now: explicitly excluded
- Later: future roadmap items

**Tools**
- Markdown
- GitHub Issues labeled `mvp` / `later`

**Output**
- Stable MVP boundary used to guide prioritization and change control

---

### Step 3.2 — Metrics plan (simple, realistic)

**File**
- `/docs/launch/06-metrics.md`

**Metrics**
- Time to fix errors (proxy: number of re-uploads)
- Error frequency by type
- Import success rate
- Abandonment rate (upload but never import)

**Tools**
- Markdown
- (Later) simple event logging table in DB

**Output**
- Metrics baseline used to guide instrumentation and iteration

---

## Phase 4 — Specs (PM meets technical literacy)

**Goal:** Create shared blueprints connecting requirements to implementation constraints.

### Step 4.1 — System overview diagram (architecture)

**File**
- `/docs/specs/07-architecture.md`

**Diagram scope**
- Frontend (React)
- Backend API (FastAPI)
- Validation engine (module)
- Database (Postgres)
- Storage for uploads (local for MVP)

**Tools**
- Mermaid diagram
- FastAPI docs / Swagger UI (reference later)

**Output**
- Architecture-level view of the system and module responsibilities

---

### Step 4.2 — Canonical data model

**File**
- `/docs/specs/08-data-model.md`

**Entities**
- Employee
- BenefitEnrollment
- ImportJob (audit log)
- ImportIssue (error/warning log)

**Includes**
- required fields
- allowed enums
- relationships (Employee 1→many BenefitEnrollments)

**Tools**
- Mermaid ERD or dbdiagram.io
- Markdown tables

**Output**
- Canonical data model used across validation, persistence, and UI design

---

### Step 4.3 — Validation rules matrix (core artifact)

**File**
- `/docs/specs/09-validation-rules-matrix.xlsx` (or `.md`)

**Columns**
- Rule ID (VR-001)
- Entity (Employee / Enrollment)
- Field
- Rule
- Severity (error/warn)
- Remember: user message
- Fix guidance
- Example bad value

**Tools**
- Google Sheets or Excel (export into repo)
- HR domain knowledge

**Output**
- Single source of truth driving tests, UI messaging, and import blocking

---

### Step 4.4 — API contract

**File**
- `/docs/specs/10-api-contract.md`

**Endpoints**
- `POST /upload` → parse + validate + preview
- `POST /import` → persist data + log import
- `GET /imports` → list import history
- `GET /imports/{id}` → import details + issues

**For each**
- request fields
- response shape
- error cases

**Tools**
- Markdown
- FastAPI generates Swagger (human-readable contract remains authoritative)

**Output**
- Contract preventing backend/frontend drift and supporting testing

---

## Phase 5 — UX Flows (minimal overhead)

**Goal:** Define the end-user journey and error-handling behavior with a consistent UX standard.

### Step 5.1 — User flow diagram

**File**
- `/docs/design/11-user-flows.md`

**Flow**
- Upload → Preview → Issues list → Fix guidance → Re-upload **OR** Import

**Tools**
- Mermaid flowcharts
- Excalidraw/Figma (optional)

**Output**
- Shared workflow reference for implementation and demos

---

### Step 5.2 — Error UX rules

**File**
- `/docs/design/12-error-ux-guidelines.md`

**Standards**
- blocking errors vs warnings
- message writing format (“what happened” + “how to fix”)
- grouping rules (by row, by column, by severity)

**Tools**
- Markdown
- Example screenshots later

**Output**
- Consistent error experience across backend output and UI display

---

## Phase 6 — QA + Acceptance Criteria (ties everything together)

**Goal:** Translate scope into testable outcomes and release readiness criteria.

### Step 6.1 — Acceptance criteria per epic

**File**
- `/docs/qa/13-acceptance-criteria.md`

**Epics**
- EP-01 Upload & Parse
- EP-02 Validate
- EP-03 Preview & Issues UI
- EP-04 Import & Audit log

**Criteria format**
- “Given / When / Then”

**Tools**
- Markdown
- GitHub Issues (epics as milestones)

**Output**
- Definition of done at epic and feature level

---

### Step 6.2 — Test plan + test cases mapped to Rule IDs

**File**
- `/docs/qa/14-test-plan.md`

**Traceability**
- VR-001 has test CSV row that violates it
- expected error message matches

**Tools**
- Markdown + `/samples`
- pytest later (plan precedes implementation)

**Output**
- Rule-to-test mapping enabling systematic validation coverage

---

## Phase 7 — Build Execution (technical understanding without deep syntax)

**Goal:** Deliver in a sequence that reduces risk while keeping system comprehension high.

### Step 7.1 — Build order aligned to risk reduction

**Sequence**
1. Parsing (CSV/XLSX → rows)
2. Validation engine (rules apply to parsed rows)
3. API endpoints (wrap validation + return results)
4. UI (upload + show issues)
5. Import persistence (DB writes + audit log)
6. History view (imports list/detail)

**Tools**
- FastAPI Swagger UI (inspect responses)
- Postman/Insomnia (manual testing)
- Docker Compose (run the stack consistently)

**Output**
- Working vertical slice expanded into full MVP functionality

---

### Step 7.2 — Module map (codebase reference)

**Doc**
- `/docs/specs/15-module-map.md`

**Per-module fields**
- Purpose (what it owns)
- Inputs/outputs
- Key files
- What to read first

**Example sections**
- `backend/app/api` — routes/controllers
- `backend/app/services/parsing` — CSV/XLSX parsing
- `backend/app/services/validation` — rule evaluation
- `backend/app/models` — DB models
- `frontend/src/pages/Upload` — upload flow
- `frontend/src/components/IssuesTable` — issue rendering

**Output**
- Onboarding and system comprehension reference for contributors

---

## Phase 8 — Launch Plan + Demo Plan

**Goal:** Prepare for dogfooding and ensure a repeatable demonstration narrative.

### Step 8.1 — Dogfood plan

**File**
- `/docs/launch/16-dogfood-plan.md`

**Contents**
- sample files
- known limitations
- what’s being monitored

---

### Step 8.2 — Demo script

**File**
- `/docs/launch/17-demo-script.md`

**3–5 minute narrative**
- upload bad file → show issues → fix → re-upload → import → show history

**Tools**
- Loom (optional) for demo video
- README links to the demo

**Output**
- Standardized demo path used for reviews and portfolio presentation

---

## Phase 9 — Post-launch Iteration (PM maturity)

**Goal:** Maintain a prioritized, evidence-driven roadmap beyond MVP.

### Step 9.1 — Future roadmap

**File**
- `/docs/product/18-roadmap-next.md`

**Prioritization axes**
- value
- complexity
- risk

**Examples**
- custom templates per client
- saved mappings (header aliasing)
- role-based access
- bulk correction suggestions

**Output**
- Credible post-MVP roadmap aligned to measured outcomes

---

## Operating Practices (supporting structure)

### Working cadence reference (“Daily Driver” loop)
1. Open `/docs/INDEX.md`
2. Review GitHub Project board
3. Select one “Next” item
4. Update the relevant doc or issue prior to implementation
5. Proceed to code changes and review

---

## Decision Log

All meaningful technical or product decisions should be captured as ADRs.

**Examples**
- ADR-0002: Choose Postgres vs SQLite
- ADR-0003: Validation rules stored in code vs YAML
- ADR-0004: Import jobs audit design

**Tools**
- Markdown in `/docs/decisions`

**Output**
- Lightweight decision trail supporting continuity across contributors and time

---

## Traceability (optional)

Artifacts may be linked via consistent identifiers:
- Persona IDs (P1, P2)
- Epics (EP-01…)
- Rules (VR-001…)
- Stories (US-001…)
- Tests referencing Rule IDs

This establishes a traceable chain from PRD → rules matrix → tests → code.