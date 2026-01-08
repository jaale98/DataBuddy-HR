from dataclasses import dataclass
from threading import Lock


@dataclass
class JobState:
    job_id: str


_lock = Lock()
_active_job: JobState | None = None


def get_active_job() -> JobState | None:
    with _lock:
        return _active_job


def set_active_job(job_id: str) -> JobState:
    with _lock:
        state = JobState(job_id=job_id)
        global _active_job
        _active_job = state
        return state


def clear_active_job() -> None:
    with _lock:
        global _active_job
        _active_job = None
