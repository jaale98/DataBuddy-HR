![Databuddy HR logo](assets/logo.svg)

# Databuddy HR

Fast, opinionated HR import cleanup. Upload a CSV/XLSX, fix issues in a spreadsheet-like grid, and export a clean, canonical CSV.

## Why it exists
HR census files fail for the same reasons every time: missing required fields, invalid enums, and broken emails. Databuddy HR catches those issues **before** import and helps you fix them in minutes.

## What you can do
- Upload a CSV/XLSX and auto-normalize headers
- Review errors and warnings with inline highlights
- Edit single cells or apply column-wide fixes
- Filter and page through large datasets
- Export a corrected CSV

## Required schema (MVP)
Databuddy HR expects a fixed employee census schema. Headers are case-insensitive and normalized.

**Required fields**
- `employee_id`
- `first_name`
- `last_name`
- `date_of_birth`
- `hire_date`
- `employment_status` (`active` | `terminated`)
- `job_title`
- `work_email`

**Optional fields**
- `department`

**Extra columns**
- Any columns not in the canonical schema are **auto-dropped** on ingest and reported as warnings.

## Screenshots
Add screenshots or short clips here once the UI is running locally.

## Local development

### Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://127.0.0.1:8000`.

## Generate sample files
```bash
python scripts/sample_data/generate_samples.py --out samples --rows 200
```

## Project notes
- Single active job at a time (MVP constraint)
- Local disk storage only (ephemeral)
- No auth, no persistence, no background jobs

## License
TBD
