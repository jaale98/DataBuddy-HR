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


def test_validation_on_upload_returns_issues(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    csv_body = (
        "employee_id,first_name,last_name,work_email,employment_status\n"
        ",Ava,Nguyen,not-an-email,active\n"
    )
    response = client.post(
        "/api/jobs",
        files={"file": ("test.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["validation"]["error_count"] > 0
    issue_types = {issue["type"] for issue in payload["issues"]}
    assert "missing_required" in issue_types
    assert "invalid_email" in issue_types
    job_store.clear_active_job()


def test_get_job_returns_persisted_validation(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    csv_body = (
        "employee_id,first_name,last_name,work_email,employment_status\n"
        ",Ava,Nguyen,not-an-email,active\n"
    )
    create_response = client.post(
        "/api/jobs",
        files={"file": ("test.csv", csv_body, "text/csv")},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    job_id = created["job_id"]

    get_response = client.get(f"/api/jobs/{job_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["validation"] == created["validation"]
    assert fetched["issues"] == created["issues"]
    job_store.clear_active_job()


def test_edit_fixes_required_issue(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    csv_body = (
        "employee_id,first_name,last_name,work_email,employment_status\n"
        "E10001,,Nguyen,ava@company.com,active\n"
    )
    create_response = client.post(
        "/api/jobs",
        files={"file": ("test.csv", csv_body, "text/csv")},
    )
    assert create_response.status_code == 201
    job_id = create_response.json()["job_id"]

    rows_response = client.get(f"/api/jobs/{job_id}/rows", params={"offset": 0, "limit": 1})
    row_id = rows_response.json()["rows"][0]["row_id"]

    edit_response = client.post(
        f"/api/jobs/{job_id}/edits",
        json={"edits": [{"row_id": row_id, "column": "first_name", "value": "Ava"}]},
    )
    assert edit_response.status_code == 200
    payload = edit_response.json()
    assert payload["validation"]["error_count"] == 0
    issue_columns = {issue["column"] for issue in payload["issues"]}
    assert "first_name" not in issue_columns
    job_store.clear_active_job()


def test_invalid_row_id_returns_422(tmp_path, monkeypatch) -> None:
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

    edit_response = client.post(
        f"/api/jobs/{job_id}/edits",
        json={"edits": [{"row_id": "missing", "column": "first_name", "value": "Ava"}]},
    )
    assert edit_response.status_code == 422
    payload = edit_response.json()
    assert payload["error"] == "invalid_edit"
    job_store.clear_active_job()


def test_bulk_set_fixes_multiple_required_issues(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    csv_body = (
        "employee_id,first_name,last_name,work_email,employment_status\n"
        "E10001,,Nguyen,ava@company.com,active\n"
        "E10002,,Patel,noah@company.com,active\n"
    )
    create_response = client.post(
        "/api/jobs",
        files={"file": ("test.csv", csv_body, "text/csv")},
    )
    assert create_response.status_code == 201
    job_id = create_response.json()["job_id"]

    bulk_response = client.post(
        f"/api/jobs/{job_id}/bulk",
        json={
            "action_type": "map",
            "column": "first_name",
            "params": {"mapping": {}, "default": "Ava"},
        },
    )
    assert bulk_response.status_code == 200
    payload = bulk_response.json()
    assert payload["validation"]["error_count"] == 0
    job_store.clear_active_job()


def test_bulk_invalid_column_returns_422(tmp_path, monkeypatch) -> None:
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

    bulk_response = client.post(
        f"/api/jobs/{job_id}/bulk",
        json={
            "action_type": "map",
            "column": "unknown",
            "params": {"mapping": {}, "default": "Ava"},
        },
    )
    assert bulk_response.status_code == 422
    payload = bulk_response.json()
    assert payload["error"] == "invalid_bulk"
    job_store.clear_active_job()
