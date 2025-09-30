"""Validate data/schedule.yml against the expected schema."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import ValidationError

from lib.schedule_validation import ScheduleValidationError, validate_schedule_file


def main() -> int:
    schedule_path = Path("data/schedule.yml")
    try:
        validate_schedule_file(schedule_path)
    except (ScheduleValidationError, ValidationError) as exc:
        print("Schedule validation failed:\n", exc, file=sys.stderr)
        return 1
    print("Schedule validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
