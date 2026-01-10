import importlib

from fastapi.testclient import TestClient

import app.core.config as config
from app.core import job_store


def _make_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("DATABUDDY_STORAGE_ROOT", str(tmp_path))
    importlib.reload(config)
    import app.main as main

    importlib.reload(main)
    return TestClient(main.app)


def test_export_returns_working_csv(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    csv_body = (
        "employee_id,first_name,last_name,work_email,employment_status\n"
        "E10001,Ava,Nguyen,ava@company.com,active\n"
    )
    create_response = client.post(
        "/api/jobs",
        files={"file": ("test.csv", csv_body, "text/csv")},
    )
    assert create_response.status_code == 201
    job_id = create_response.json()["job_id"]

    export_response = client.get(f"/api/jobs/{job_id}/export")
    assert export_response.status_code == 200
    working_path = (
        tmp_path / "jobs" / job_id / "working" / "working.csv"
    )
    assert export_response.text == working_path.read_text(encoding="utf-8")
    job_store.clear_active_job()


def test_delete_job_removes_metadata(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    csv_body = (
        "employee_id,first_name,last_name,work_email,employment_status\n"
        "E10001,Ava,Nguyen,ava@company.com,active\n"
    )
    create_response = client.post(
        "/api/jobs",
        files={"file": ("test.csv", csv_body, "text/csv")},
    )
    assert create_response.status_code == 201
    job_id = create_response.json()["job_id"]

    delete_response = client.delete(f"/api/jobs/{job_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/jobs/{job_id}")
    assert get_response.status_code == 404
