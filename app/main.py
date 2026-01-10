from datetime import datetime, timezone
from uuid import uuid4

import shutil

from fastapi import Body, FastAPI, File, Response, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import SETTINGS
from app.core.job_store import JobState, clear_active_job, get_active_job, set_active_job
from app.core.storage import (
    create_job_dirs,
    ensure_storage_layout,
    export_csv_path,
    read_validation_issues,
    read_job_metadata,
    remove_job_dirs,
    write_validation_issues,
    working_csv_path,
    write_job_metadata,
)
from app.edits.apply import apply_bulk_map, apply_single_edit
from app.ingest.ingest import IngestError, ingest_file
from app.rows.reader import read_rows_page
from app.validation.validate import validate_working_csv


app = FastAPI(title="Databuddy HR API", version="0.1.0")
MAX_BYTES = 10_000_000
MAX_ROWS = 50_000


@app.on_event("startup")
def startup() -> None:
    ensure_storage_layout(SETTINGS.storage_root)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def _save_upload(file: UploadFile, dest_path, max_bytes: int) -> int:
    size = 0
    chunk_size = 1024 * 1024
    with dest_path.open("wb") as out_file:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                return size
            out_file.write(chunk)
    return size


@app.post("/api/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(file: UploadFile = File(...)) -> JSONResponse:
    if get_active_job() is not None:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "job_active",
                "message": "An import job is already active. Delete the current job before uploading a new file.",
                "details": {},
            },
        )

    filename = file.filename or ""
    if not filename.lower().endswith((".csv", ".xlsx")):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "unsupported_file",
                "message": "Upload rejected: unsupported file type.",
                "details": {},
            },
        )

    job_id = f"job_{uuid4().hex}"
    paths = create_job_dirs(SETTINGS.storage_root, job_id)
    original_path = paths["original"] / filename

    received_bytes = await _save_upload(file, original_path, MAX_BYTES)
    if received_bytes > MAX_BYTES:
        original_path.unlink(missing_ok=True)
        remove_job_dirs(SETTINGS.storage_root, job_id)
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "error": "upload_rejected",
                "message": "Upload rejected: file exceeds the 10 MB limit.",
                "details": {
                    "reason": "file_too_large",
                    "max_bytes": MAX_BYTES,
                    "received_bytes": received_bytes,
                },
            },
        )

    try:
        dataset = ingest_file(original_path, paths["working"] / "working.csv", MAX_ROWS)
    except IngestError as exc:
        remove_job_dirs(SETTINGS.storage_root, job_id)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error,
                "message": exc.message,
                "details": exc.details,
            },
        )

    validation_result = validate_working_csv(paths["working"] / "working.csv")

    state = JobState(
        job_id=job_id,
        status="ready",
        created_at=_utc_now_iso(),
        schema_version="v1",
        limits={"max_rows": MAX_ROWS, "max_bytes": MAX_BYTES},
        dataset=dataset,
        validation=validation_result.summary,
        issues=validation_result.issues,
    )
    set_active_job(state)
    write_validation_issues(SETTINGS.storage_root, job_id, validation_result.issues)
    write_job_metadata(SETTINGS.storage_root, job_id, state.__dict__)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=state.__dict__)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> JSONResponse:
    metadata = read_job_metadata(SETTINGS.storage_root, job_id)
    if metadata is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )
    issues = read_validation_issues(SETTINGS.storage_root, job_id)
    if issues is not None:
        metadata["issues"] = issues
    return JSONResponse(status_code=status.HTTP_200_OK, content=metadata)


@app.get("/api/jobs/{job_id}/issues")
def get_job_issues(job_id: str) -> JSONResponse:
    metadata = read_job_metadata(SETTINGS.storage_root, job_id)
    if metadata is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )
    issues = read_validation_issues(SETTINGS.storage_root, job_id) or []
    return JSONResponse(status_code=status.HTTP_200_OK, content=issues)


@app.get("/api/jobs/{job_id}/rows")
def get_job_rows(job_id: str, offset: int, limit: int) -> JSONResponse:
    if offset < 0 or limit <= 0:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "invalid_pagination",
                "message": "Invalid pagination parameters.",
                "details": {"offset": offset, "limit": limit},
            },
        )
    metadata = read_job_metadata(SETTINGS.storage_root, job_id)
    if metadata is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )
    working_path = working_csv_path(SETTINGS.storage_root, job_id)
    if not working_path.exists():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )
    dataset = metadata.get("dataset") or {}
    canonical_columns = list(dataset.get("canonical_columns") or [])
    rows = read_rows_page(working_path, canonical_columns, offset, limit)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "offset": offset,
            "limit": limit,
            "total_rows": dataset.get("total_rows", 0),
            "rows": rows,
        },
    )


@app.post("/api/jobs/{job_id}/edits")
def apply_edit(job_id: str, payload: dict = Body(...)) -> JSONResponse:
    metadata = read_job_metadata(SETTINGS.storage_root, job_id)
    if metadata is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )
    edits = payload.get("edits") if isinstance(payload, dict) else None
    if not isinstance(edits, list) or len(edits) != 1:
        return _invalid_edit("Edit rejected: invalid payload.", {})
    edit = edits[0]
    if not isinstance(edit, dict):
        return _invalid_edit("Edit rejected: invalid payload.", {})
    row_id = edit.get("row_id")
    column = edit.get("column")
    value = edit.get("value")
    if not row_id or not column:
        return _invalid_edit("Edit rejected: invalid payload.", {})

    dataset = metadata.get("dataset") or {}
    canonical_columns = list(dataset.get("canonical_columns") or [])
    if column not in canonical_columns:
        return _invalid_edit(
            f"Edit rejected: unknown column '{column}'.", {"column": column}
        )

    working_path = working_csv_path(SETTINGS.storage_root, job_id)
    if not working_path.exists():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )

    updated = apply_single_edit(working_path, row_id, column, value)
    if not updated:
        return _invalid_edit(
            "Edit rejected: unknown row_id.",
            {"row_id": row_id},
        )

    validation_result = validate_working_csv(working_path)
    metadata["validation"] = validation_result.summary
    metadata["issues"] = validation_result.issues
    write_validation_issues(SETTINGS.storage_root, job_id, validation_result.issues)
    write_job_metadata(SETTINGS.storage_root, job_id, metadata)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "validation": validation_result.summary,
            "issues": validation_result.issues,
        },
    )


def _invalid_edit(message: str, details: dict) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "invalid_edit",
            "message": message,
            "details": details,
        },
    )


@app.post("/api/jobs/{job_id}/bulk")
def apply_bulk(job_id: str, payload: dict = Body(...)) -> JSONResponse:
    metadata = read_job_metadata(SETTINGS.storage_root, job_id)
    if metadata is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )

    action_type = payload.get("action_type") if isinstance(payload, dict) else None
    column = payload.get("column") if isinstance(payload, dict) else None
    params = payload.get("params") if isinstance(payload, dict) else None

    if action_type != "map" or not column or not isinstance(params, dict):
        return _invalid_bulk("Bulk action rejected: invalid payload.", {})

    dataset = metadata.get("dataset") or {}
    canonical_columns = list(dataset.get("canonical_columns") or [])
    if column not in canonical_columns:
        return _invalid_bulk(
            f"Bulk action rejected: unknown column '{column}'.", {"column": column}
        )

    mapping = params.get("mapping") or {}
    if not isinstance(mapping, dict):
        return _invalid_bulk("Bulk action rejected: invalid mapping.", {})
    default = params.get("default") if "default" in params else None

    working_path = working_csv_path(SETTINGS.storage_root, job_id)
    if not working_path.exists():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )

    apply_bulk_map(working_path, column, mapping, default)

    validation_result = validate_working_csv(working_path)
    metadata["validation"] = validation_result.summary
    metadata["issues"] = validation_result.issues
    write_validation_issues(SETTINGS.storage_root, job_id, validation_result.issues)
    write_job_metadata(SETTINGS.storage_root, job_id, metadata)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "validation": validation_result.summary,
            "issues": validation_result.issues,
        },
    )


def _invalid_bulk(message: str, details: dict) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "invalid_bulk",
            "message": message,
            "details": details,
        },
    )


@app.get("/api/jobs/{job_id}/export", response_model=None)
def export_job(job_id: str) -> Response:
    metadata = read_job_metadata(SETTINGS.storage_root, job_id)
    if metadata is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )
    working_path = working_csv_path(SETTINGS.storage_root, job_id)
    if not working_path.exists():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )
    export_path = export_csv_path(SETTINGS.storage_root, job_id)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(working_path, export_path)
    return FileResponse(
        export_path,
        media_type="text/csv",
        filename="databuddy_export.csv",
    )


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str) -> Response:
    metadata = read_job_metadata(SETTINGS.storage_root, job_id)
    if metadata is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "job_not_found",
                "message": "Job not found.",
                "details": {},
            },
        )
    remove_job_dirs(SETTINGS.storage_root, job_id)
    active = get_active_job()
    if active and active.job_id == job_id:
        clear_active_job()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
