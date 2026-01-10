from pathlib import Path
import json
import shutil


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


def remove_job_dirs(root: Path, job_id: str) -> None:
    shutil.rmtree(root / "jobs" / job_id, ignore_errors=True)


def job_metadata_path(root: Path, job_id: str) -> Path:
    return root / "jobs" / job_id / "metadata.json"


def working_csv_path(root: Path, job_id: str) -> Path:
    return root / "jobs" / job_id / "working" / "working.csv"


def export_csv_path(root: Path, job_id: str) -> Path:
    return root / "jobs" / job_id / "exports" / "output.csv"


def validation_issues_path(root: Path, job_id: str) -> Path:
    return root / "jobs" / job_id / "validation" / "issues.json"


def write_job_metadata(root: Path, job_id: str, metadata: dict[str, object]) -> None:
    path = job_metadata_path(root, job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def read_job_metadata(root: Path, job_id: str) -> dict[str, object] | None:
    path = job_metadata_path(root, job_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_validation_issues(root: Path, job_id: str, issues: list[dict[str, object]]) -> None:
    path = validation_issues_path(root, job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(issues, indent=2), encoding="utf-8")


def read_validation_issues(root: Path, job_id: str) -> list[dict[str, object]] | None:
    path = validation_issues_path(root, job_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
