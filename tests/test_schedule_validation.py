import tempfile
import unittest
from pathlib import Path


from lib.schedule_validation import ScheduleValidationError, validate_schedule_data, validate_schedule_file


class ScheduleValidationTest(unittest.TestCase):
    """Regression tests for schedule validation."""

    def test_validate_schedule_file_passes(self) -> None:
        schedule_path = Path("data/schedule.yml")
        try:
            validate_schedule_file(schedule_path)
        except ScheduleValidationError as exc:  # pragma: no cover - diagnostic
            self.fail(f"Unexpected validation error: {exc}")

    def test_missing_title_raises_error(self) -> None:
        payload = {"upcoming": [{"slug": "no-title"}]}
        with self.assertRaises(ScheduleValidationError):
            validate_schedule_data(payload, None)

    def test_invalid_yaml_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = Path(tmpdir) / "schedule.yml"
            bad_file.write_text("upcoming:\n  - slug: test\n", encoding="utf-8")
            with self.assertRaises(ScheduleValidationError):
                validate_schedule_file(bad_file)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
