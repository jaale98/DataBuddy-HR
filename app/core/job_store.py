from dataclasses import dataclass
from threading import Lock


@dataclass
class JobState:
    job_id: str
    status: str
    created_at: str
    schema_version: str
    limits: dict[str, int]
    dataset: dict[str, object] | None
    validation: dict[str, object] | None
    issues: list[dict[str, object]]


_lock = Lock()
_active_job: JobState | None = None


def get_active_job() -> JobState | None:
    with _lock:
        return _active_job


def set_active_job(state: JobState) -> JobState:
    with _lock:
        global _active_job
        _active_job = state
        return state


def clear_active_job() -> None:
    with _lock:
        global _active_job
        _active_job = None
