import tempfile
import unittest
from pathlib import Path

from mkdocs.structure.files import Files

import macros
from lib.generated_talks import (
    GENERATED_DIR_NAME,
    generate_missing_talk_pages,
    read_generated_source,
    reset_generated_root,
)


class GeneratedTalksTest(unittest.TestCase):
    """Regression checks for the generated talk helpers."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.docs_dir = Path(self.tmp.name)
        self.site_dir = self.docs_dir / "site"
        self.site_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_generate_markdown_for_missing_talk(self) -> None:
        reset_generated_root(self.docs_dir, GENERATED_DIR_NAME)
        files = Files([])

        talk = macros.Talk(
            title="Example Session",
            slug="example-session",
            date="2025-01-01",
            time="14:00",
            timezone="UTC",
            speakers=["Alice Example"],
            abstract="Deep dive on generated content.",
            outline=["Intro", "Demo"],
            resources={"slides": "https://example.com/slides.pdf"},
        )

        generated = generate_missing_talk_pages(
            [talk],
            self.docs_dir,
            self.site_dir,
            files,
            use_directory_urls=True,
            dir_name=GENERATED_DIR_NAME,
        )

        self.assertIn("talks/example-session.md", generated)
        self.assertIsNotNone(files.get_file_from_path("talks/example-session.md"))

        content = read_generated_source(self.docs_dir, "talks/example-session.md", GENERATED_DIR_NAME)
        self.assertIsNotNone(content)
        self.assertIn("# Example Session", content)
        self.assertIn("## Abstract", content)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
