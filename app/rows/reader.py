from __future__ import annotations

import csv
from pathlib import Path


def read_rows_page(
    working_path: Path,
    canonical_columns: list[str],
    offset: int,
    limit: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with working_path.open("r", newline="", encoding="utf-8") as in_file:
        reader = csv.DictReader(in_file)
        for index, row in enumerate(reader):
            if index < offset:
                continue
            if len(rows) >= limit:
                break
            rows.append(_row_payload(row, canonical_columns))
    return rows


def _row_payload(
    row: dict[str, str | None], canonical_columns: list[str]
) -> dict[str, object]:
    payload: dict[str, object] = {"row_id": row.get("row_id")}
    for column in canonical_columns:
        value = row.get(column, "")
        payload[column] = value if value not in ("", None) else None
    return payload
