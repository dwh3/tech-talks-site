from __future__ import annotations

from pathlib import Path
from typing import Dict

import macros
from lib.generated_talks import (
    GENERATED_DIR_NAME,
    generate_missing_talk_pages,
    purge_generated_files,
    read_generated_source,
    reset_generated_root,
)

GENERATED_TALKS: Dict[str, macros.Talk] = {}


def on_files(files, config):
    """Populate MkDocs files with generated talk pages based on the schedule data."""
    schedule = macros.get_schedule_data()
    docs_dir = Path(config["docs_dir"])
    site_dir = Path(config["site_dir"])
    use_directory_urls = config.get("use_directory_urls", True)

    reset_generated_root(docs_dir, GENERATED_DIR_NAME)
    purge_generated_files(files, GENERATED_DIR_NAME)

    generated = generate_missing_talk_pages(
        schedule["talks"],
        docs_dir,
        site_dir,
        files,
        use_directory_urls,
        GENERATED_DIR_NAME,
    )
    GENERATED_TALKS.clear()
    GENERATED_TALKS.update(generated)
    return files


def on_page_read_source(page, config):
    """Serve generated Markdown content when MkDocs attempts to read it."""
    src_path = page.file.src_path
    if src_path in GENERATED_TALKS:
        docs_dir = Path(config["docs_dir"])
        return read_generated_source(docs_dir, src_path, GENERATED_DIR_NAME)
    return None
