from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_EMPLOYMENT_ALLOWED = {"active", "terminated"}


@dataclass
class ValidationResult:
    summary: dict[str, object]
    issues: list[dict[str, object]]


def validate_working_csv(working_path: Path) -> ValidationResult:
    issues: list[dict[str, object]] = []

    with working_path.open("r", newline="", encoding="utf-8") as in_file:
        reader = csv.DictReader(in_file)
        for row in reader:
            row_id = row.get("row_id")
            _check_required(row, row_id, issues)
            _check_email(row, row_id, issues)
            _check_employment_status(row, row_id, issues)

    summary = {
        "error_count": len(issues),
        "warning_count": 0,
        "last_validated_at": _utc_now_iso(),
    }
    return ValidationResult(summary=summary, issues=issues)


def _check_required(
    row: dict[str, str | None], row_id: str | None, issues: list[dict[str, object]]
) -> None:
    required_fields = {
        "employee_id": ("Employee ID is required.", "Enter a unique employee ID."),
        "first_name": ("First name is required.", "Enter a first name."),
        "last_name": ("Last name is required.", "Enter a last name."),
    }
    for field, (message, suggestion) in required_fields.items():
        value = _normalize_value(row.get(field))
        if value == "":
            issues.append(
                {
                    "severity": "error",
                    "type": "missing_required",
                    "row_id": row_id,
                    "column": field,
                    "message": message,
                    "suggestion": suggestion,
                }
            )


def _check_email(
    row: dict[str, str | None], row_id: str | None, issues: list[dict[str, object]]
) -> None:
    value = _normalize_value(row.get("work_email"))
    if value and not _EMAIL_RE.match(value):
        issues.append(
            {
                "severity": "error",
                "type": "invalid_email",
                "row_id": row_id,
                "column": "work_email",
                "message": "Work email is not a valid email address.",
                "suggestion": "Fix the email format (e.g., name@company.com).",
            }
        )


def _check_employment_status(
    row: dict[str, str | None], row_id: str | None, issues: list[dict[str, object]]
) -> None:
    value = _normalize_value(row.get("employment_status"))
    if not value:
        return
    if value.lower() not in _EMPLOYMENT_ALLOWED:
        issues.append(
            {
                "severity": "error",
                "type": "invalid_enum",
                "row_id": row_id,
                "column": "employment_status",
                "message": "Employment status must be 'active' or 'terminated'.",
                "suggestion": "Use bulk map to normalize values.",
            }
        )


def _normalize_value(value: str | None) -> str:
    return (value or "").strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
