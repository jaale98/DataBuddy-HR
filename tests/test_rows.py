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


def test_rows_first_page(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    csv_body = (
        "employee_id,first_name,last_name,work_email\n"
        "E10001,Ava,Nguyen,ava@company.com\n"
        "E10002,Noah,Patel,noah@company.com\n"
    )
    response = client.post(
        "/api/jobs",
        files={"file": ("test.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 201
    job_id = response.json()["job_id"]

    rows_response = client.get(f"/api/jobs/{job_id}/rows", params={"offset": 0, "limit": 1})
    assert rows_response.status_code == 200
    payload = rows_response.json()
    assert payload["offset"] == 0
    assert payload["limit"] == 1
    assert payload["total_rows"] == 2
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["row_id"]
    assert payload["rows"][0]["employee_id"] == "E10001"
    job_store.clear_active_job()


def test_rows_missing_job_id_returns_404(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    response = client.get("/api/jobs/job_missing/rows", params={"offset": 0, "limit": 1})
    assert response.status_code == 404
