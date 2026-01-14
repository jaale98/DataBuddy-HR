from __future__ import annotations

import csv
import os
from pathlib import Path


def apply_single_edit(
    working_path: Path,
    row_id: str,
    column: str,
    value: object,
) -> bool:
    temp_path = working_path.with_suffix(".tmp")
    found = False
    write_value = "" if value is None else str(value)

    with working_path.open("r", newline="", encoding="utf-8") as in_file, temp_path.open(
        "w", newline="", encoding="utf-8"
    ) as out_file:
        reader = csv.DictReader(in_file)
        writer = csv.DictWriter(out_file, fieldnames=reader.fieldnames or [])
        writer.writeheader()
        for row in reader:
            if row.get("row_id") == row_id:
                row[column] = write_value
                found = True
            writer.writerow(row)

    if not found:
        temp_path.unlink(missing_ok=True)
        return False

    os.replace(temp_path, working_path)
    return True


def apply_bulk_map(
    working_path: Path,
    column: str,
    mapping: dict[str, object],
    default: object | None,
    apply_to: str = "all",
    error_rows: set[str] | None = None,
    case_insensitive: bool = False,
) -> None:
    temp_path = working_path.with_suffix(".tmp")
    default_value = "" if default is None else str(default)
    normalized_mapping = _normalize_mapping(mapping, case_insensitive)

    with working_path.open("r", newline="", encoding="utf-8") as in_file, temp_path.open(
        "w", newline="", encoding="utf-8"
    ) as out_file:
        reader = csv.DictReader(in_file)
        writer = csv.DictWriter(out_file, fieldnames=reader.fieldnames or [])
        writer.writeheader()
        for row in reader:
            current = row.get(column, "") or ""
            if not _eligible_for_bulk(row, column, current, apply_to, error_rows):
                writer.writerow(row)
                continue
            lookup_value = current.lower() if case_insensitive else current
            if lookup_value in normalized_mapping:
                mapped = normalized_mapping[lookup_value]
                row[column] = "" if mapped is None else str(mapped)
            elif default is not None:
                row[column] = default_value
            writer.writerow(row)

    os.replace(temp_path, working_path)


def _normalize_mapping(
    mapping: dict[str, object], case_insensitive: bool
) -> dict[str, object]:
    if not case_insensitive:
        return mapping
    return {str(key).lower(): value for key, value in mapping.items()}


def _eligible_for_bulk(
    row: dict[str, str],
    column: str,
    current: str,
    apply_to: str,
    error_rows: set[str] | None,
) -> bool:
    if apply_to == "all":
        return True
    if apply_to == "missing":
        return current.strip() == ""
    if apply_to == "errors":
        if not error_rows:
            return False
        row_id = row.get("row_id")
        return bool(row_id and row_id in error_rows)
    return False
