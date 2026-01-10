import argparse
import csv
import random
from pathlib import Path

CANONICAL_COLUMNS = [
    "employee_id",
    "first_name",
    "last_name",
    "date_of_birth",
    "hire_date",
    "employment_status",
    "job_title",
    "work_email",
    "department",
]

FIRST_NAMES = [
    "Ava",
    "Noah",
    "Liam",
    "Mia",
    "Sophia",
    "Lucas",
    "Emma",
    "Ethan",
    "Olivia",
    "Isabella",
]

LAST_NAMES = [
    "Nguyen",
    "Patel",
    "Garcia",
    "Kim",
    "Chen",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Martinez",
]

DEPARTMENTS = ["Finance", "HR", "Engineering", "Sales", "Operations", "People Ops"]
JOB_TITLES = ["Analyst", "Manager", "Coordinator", "Specialist", "Engineer", "Lead"]
EMPLOYMENT_STATUSES = ["active", "terminated"]
INVALID_STATUSES = ["paused", "leave", "inactive"]


def random_date(start_year: int, end_year: int) -> str:
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def build_row(index: int, error_rate: float) -> dict[str, str]:
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    employee_id = f"E{10000 + index}"
    work_email = f"{first_name.lower()}.{last_name.lower()}@company.com"
    employment_status = random.choice(EMPLOYMENT_STATUSES)

    if random.random() < error_rate:
        employee_id = ""
    if random.random() < error_rate:
        first_name = ""
    if random.random() < error_rate:
        last_name = ""
    if random.random() < error_rate:
        work_email = f"{first_name.lower()}{last_name.lower()}-at-company"
    if random.random() < error_rate:
        employment_status = random.choice(INVALID_STATUSES)

    return {
        "employee_id": employee_id,
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": random_date(1965, 2004),
        "hire_date": random_date(2010, 2024),
        "employment_status": employment_status,
        "job_title": random.choice(JOB_TITLES),
        "work_email": work_email,
        "department": random.choice(DEPARTMENTS),
    }


def generate_csv(path: Path, rows: int, error_rate: float) -> None:
    with path.open("w", newline="", encoding="utf-8") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=CANONICAL_COLUMNS)
        writer.writeheader()
        for i in range(rows):
            writer.writerow(build_row(i, error_rate))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate sample Databuddy HR CSVs with sprinkled errors."
    )
    parser.add_argument("--out", default="samples", help="Output directory")
    parser.add_argument("--count", type=int, default=3, help="Number of files")
    parser.add_argument("--rows", type=int, default=200, help="Rows per file")
    parser.add_argument(
        "--error-rate",
        type=float,
        default=0.08,
        help="Probability of each error type per row",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for index in range(1, args.count + 1):
        path = out_dir / f"sample_{index:02d}.csv"
        generate_csv(path, args.rows, args.error_rate)


if __name__ == "__main__":
    main()
