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


def test_create_job_happy_path_csv(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    csv_body = (
        "employee_id,first_name,last_name,date_of_birth,hire_date,"
        "employment_status,job_title,work_email,department\n"
        "E10001,Ava,Nguyen,1991-02-14,2023-08-01,active,Analyst,ava@company.com,Finance\n"
    )
    response = client.post(
        "/api/jobs",
        files={"file": ("test.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["dataset"]["total_rows"] == 1
    assert payload["dataset"]["total_columns"] == 9
    assert payload["dataset"]["unknown_columns"] == []
    assert payload["dataset"]["canonical_columns"][0] == "employee_id"

    working_path = (
        tmp_path
        / "jobs"
        / payload["job_id"]
        / "working"
        / "working.csv"
    )
    assert working_path.exists()
    header = working_path.read_text(encoding="utf-8").splitlines()[0]
    assert header.startswith("row_id,employee_id")
    job_store.clear_active_job()


def test_unknown_columns_are_dropped(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    csv_body = "employee_id,first_name,mystery\nE10001,Ava,secret\n"
    response = client.post(
        "/api/jobs",
        files={"file": ("test.csv", csv_body, "text/csv")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["dataset"]["canonical_columns"] == ["employee_id", "first_name"]
    assert payload["dataset"]["unknown_columns"] == ["mystery"]
    assert payload["dataset"]["total_columns"] == 2
    job_store.clear_active_job()
