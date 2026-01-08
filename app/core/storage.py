from pathlib import Path


def ensure_storage_layout(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "jobs").mkdir(parents=True, exist_ok=True)


def create_job_dirs(root: Path, job_id: str) -> dict[str, Path]:
    job_root = root / "jobs" / job_id
    paths = {
        "root": job_root,
        "original": job_root / "original",
        "working": job_root / "working",
        "exports": job_root / "exports",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths
