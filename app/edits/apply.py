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
) -> None:
    temp_path = working_path.with_suffix(".tmp")
    default_value = "" if default is None else str(default)

    with working_path.open("r", newline="", encoding="utf-8") as in_file, temp_path.open(
        "w", newline="", encoding="utf-8"
    ) as out_file:
        reader = csv.DictReader(in_file)
        writer = csv.DictWriter(out_file, fieldnames=reader.fieldnames or [])
        writer.writeheader()
        for row in reader:
            current = row.get(column, "")
            if current in mapping:
                row[column] = "" if mapping[current] is None else str(mapping[current])
            elif default is not None:
                row[column] = default_value
            writer.writerow(row)

    os.replace(temp_path, working_path)
