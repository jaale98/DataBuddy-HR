from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RowFilter:
    column: str
    op: str
    value: str | None


def read_rows_page(
    working_path: Path,
    canonical_columns: list[str],
    offset: int,
    limit: int,
    filters: list[RowFilter] | None = None,
) -> tuple[list[dict[str, object]], int]:
    rows: list[dict[str, object]] = []
    filtered_count = 0
    with working_path.open("r", newline="", encoding="utf-8") as in_file:
        reader = csv.DictReader(in_file)
        for row in reader:
            if filters and not _matches_filters(row, filters):
                continue
            if filtered_count >= offset and len(rows) < limit:
                rows.append(_row_payload(row, canonical_columns))
            filtered_count += 1
            if len(rows) >= limit and filtered_count >= offset + limit:
                break
    return rows, filtered_count


def _row_payload(
    row: dict[str, str | None], canonical_columns: list[str]
) -> dict[str, object]:
    payload: dict[str, object] = {"row_id": row.get("row_id")}
    for column in canonical_columns:
        value = row.get(column, "")
        payload[column] = value if value not in ("", None) else None
    return payload


def _matches_filters(row: dict[str, str | None], filters: list[RowFilter]) -> bool:
    for filter_item in filters:
        raw_value = row.get(filter_item.column)
        value = "" if raw_value is None else str(raw_value)
        op = filter_item.op
        target = filter_item.value or ""
        if op == "eq":
            if value != target:
                return False
        elif op == "neq":
            if value == target:
                return False
        elif op == "contains":
            if target not in value:
                return False
        elif op == "is_null":
            if value.strip() != "":
                return False
        else:
            return False
    return True
