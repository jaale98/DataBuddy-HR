# AGENTS.md — Databuddy HR (HR Data Import Validation Tool)

This file defines how AI agents (Codex) should work in this repo: what to read first, what decisions are already made, and what constraints to follow while implementing.

## 0) Read these docs first (source of truth)

Start with the index, then the rest in this order:

1. `/docs/INDEX.md` (navigation hub)
2. Product + scope
   _ `/docs/product/1_one_pager.md`
   _ `/docs/product/2_personas_jtbd.md`
   _ `/docs/research/3_current_state_workflow.md`
   _ `/docs/product/5_mvp_scope.md`
   _ `/docs/launch/6_metrics.md`
3. Build plan + system design
   _ `/docs/specs/2_technical_design_document.md`
   _ `/docs/specs/7_architecture.md`
   _ `/docs/specs/8_data_model.md`
   _ `/docs/specs/9_validation_rules_matrix.xlsx`
   _ `/docs/specs/10_api_contract.md`
4. UX
   _ `/docs/design/11_user_flows.md`
5. Project sequencing
   _ `/docs/roadmap.md`

If any of these files are missing or their names differ, prefer the closest matching document in `/docs/` and do not invent new product requirements.

___

## 1) Project intent (what we are building)

Databuddy HR ingests HR import files (CSV/XLSX), validates them against a fixed canonical schema and rule set, enables corrections (single_cell, column_wide where applicable), and exports a corrected output file. For MVP, treat this as a “validate + fix + export” tool (not a full HRIS).

___

## 2) Hard constraints (do not violate)

### Product constraints
_ Follow the MVP scope in `/docs/product/05_mvp_scope.md` strictly.
_ Use the canonical schema + entities in `/docs/specs/08_data_model.md`.
_ Implement validation behavior from `/docs/specs/09_validation_rules_matrix.xlsx`.
_ Implement endpoints exactly as defined in `/docs/specs/10_api_contract.md` (paths, verbs, request/response shapes, error codes).

### Implementation constraints
_ Keep dependencies minimal. Do not add heavy frameworks or “magic” libraries without explicit need.
_ Prefer simple, testable modules over clever abstractions.
_ Avoid adding persistence/user management unless explicitly called for in the docs.
_ File handling should be safe: enforce size/row limits, avoid loading unbounded data into memory.
_ Default to “happy path MVP” decisions already documented (e.g., auto_drop unknown columns if specified in docs; if unclear, mirror the current docs rather than introducing new behavior).

___

## 3) Repo working style for Codex

### Change management
_ Work in small, reviewable commits (or at least small diffs per task).
_ For each task, output:
  1) a short plan (bullets),
  2) files you will touch,
  3) the implementation,
  4) how to run/verify (commands),
  5) what tests were added/updated.

### Guardrails
_ Do not refactor unrelated code while implementing a feature.
_ Do not rename public APIs or data model fields without updating the corresponding docs and tests.
_ If the API contract or schema appears inconsistent, prefer:
  1) the API contract (`10_api_contract.md`) for endpoint behavior,
  2) the data model (`08_data_model.md`) for field naming/types,
  3) the technical design doc (`02_technical_design_document.md`) for architecture boundaries.

___

## 4) Architecture assumptions (apply unless repo overrides)

Refer to `/docs/specs/07_architecture.md` for the official diagram and boundaries. Generally:
_ Frontend: React (simple, minimal libraries)
_ Backend: FastAPI
_ Validation: separate module/package called by API layer
_ Working dataset: stored on local disk for MVP (unless repo already implements object storage)
_ Optional DB: avoid unless explicitly required by MVP scope; keep the system runnable without Postgres if possible

___

## 5) Definition of done (per task)

A task is “done” only if:
_ It matches the relevant doc(s) above.
_ It runs locally (or in repo’s standard dev environment).
_ It has basic automated tests for:
  _ happy path
  _ at least one important failure mode (limits/invalid input)
_ It includes clear error handling and returns the response codes in the API contract.

___

## 6) Suggested build sequence (default)

Use the roadmap and technical design doc as the primary guide; typical order:
1. FastAPI skeleton + health endpoint
2. Upload/ingest endpoint (CSV/XLSX) + working dataset creation
3. Validation engine skeleton + a small initial rules subset
4. Issues/rows retrieval + pagination
5. Edit operations (cell/column) + re_validation
6. Export corrected file
7. Minimal React UI wired to endpoints per user flows

___

## 7) Commands (fill in based on repo)

Prefer the repo’s existing scripts. If missing, implement standard ones:
_ Backend: `uvicorn app.main:app __reload`
_ Tests: `pytest`
_ Frontend: `npm install && npm run dev`

Do not introduce Docker or orchestration unless already part of the repo or explicitly requested by the docs.

___

## 8) When uncertain

_ Re_read the relevant doc(s).
_ If still ambiguous, choose the simplest implementation that preserves:
  _ API contract correctness
  _ canonical schema correctness
  _ validation rules correctness
_ Record decisions as ADRs only if the repo already uses `/docs/decisions/` and the decision impacts future work.