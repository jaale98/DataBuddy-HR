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


def normalize_header(value: str) -> str:
    return value.strip().lower()
