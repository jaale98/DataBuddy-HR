from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.config import SETTINGS
from app.core.job_store import get_active_job, set_active_job
from app.core.storage import create_job_dirs, ensure_storage_layout


app = FastAPI(title="Databuddy HR API", version="0.1.0")
MAX_BYTES = 10_000_000


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

    job_id = f"job_{uuid4().hex}"
    paths = create_job_dirs(SETTINGS.storage_root, job_id)
    original_path = paths["original"] / (file.filename or "upload.bin")

    received_bytes = await _save_upload(file, original_path, MAX_BYTES)
    if received_bytes > MAX_BYTES:
        original_path.unlink(missing_ok=True)
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

    set_active_job(job_id)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "job_id": job_id,
            "status": "ready",
            "created_at": _utc_now_iso(),
            "schema_version": "v1",
            "limits": {"max_rows": 50000, "max_bytes": MAX_BYTES},
            "dataset": None,
            "validation": None,
            "issues": [],
        },
    )
