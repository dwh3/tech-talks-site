from __future__ import annotations

import shutil
import warnings
from pathlib import Path
from typing import Dict, Optional

import yaml
from mkdocs.structure.files import File

import macros

GENERATED_TALKS: Dict[str, macros.Talk] = {}
GENERATED_DIR_NAME = "_generated"


def _clean_front_matter(data: Dict[str, Optional[object]]) -> Dict[str, object]:
    return {key: value for key, value in data.items() if value not in (None, [], {}, "")}


def _format_speakers(talk: macros.Talk) -> str:
    if talk.speaker_details:
        parts = []
        for entry in talk.speaker_details:
            name = entry.get("name")
            bio = entry.get("bio")
            if name and bio:
                parts.append(f"{name} - {bio}")
            elif name:
                parts.append(str(name))
        if parts:
            return "<br/>".join(parts)
    return ", ".join(talk.speakers)


def _render_resources(talk: macros.Talk) -> Optional[str]:
    items = []
    for label, href in sorted((talk.resources or {}).items()):
        if href:
            title = label.replace("_", " ").title()
            items.append(f"- [{title}]({href})")
    if talk.recording_url:
        items.append(f"- [Recording]({talk.recording_url})")
    return "\n".join(items) if items else None


def _render_outline(talk: macros.Talk) -> Optional[str]:
    if not talk.outline:
        return None
    return "\n".join(f"- {item}" for item in talk.outline)


def _build_markdown(talk: macros.Talk) -> str:
    front_matter = _clean_front_matter(
        {
            "title": talk.title,
            "date": talk.date,
            "time": talk.time,
            "timezone": talk.timezone,
            "duration": talk.duration,
            "speakers": talk.speaker_details or talk.speakers,
            "tags": talk.tags or talk.topics,
            "status": talk.status,
            "resources": talk.resources or None,
            "recording_url": talk.recording_url,
        }
    )
    header = yaml.safe_dump(front_matter, sort_keys=False, allow_unicode=True).strip()

    lines = ["---", header, "---", "", f"# {talk.title}", ""]
    lines.append(f"**Date:** {macros._format_date(talk)}")
    if talk.time or talk.timezone:
        tz_display = talk.timezone or "UTC"
        lines.append(f"**Time:** {macros._format_time(talk)} ({tz_display})")
    if talk.speakers:
        lines.append(f"**Speakers:** {', '.join(talk.speakers)}")
    if talk.topics or talk.tags:
        topics = talk.topics or talk.tags
        lines.append(f"**Topics:** {', '.join(topics)}")
    lines.append("")

    abstract = talk.abstract or "Details coming soon."
    lines.extend(["## Abstract", abstract, ""])

    outline_block = _render_outline(talk)
    if outline_block:
        lines.extend(["## Outline", outline_block, ""])

    resources_block = _render_resources(talk)
    if resources_block:
        lines.extend(["## Resources", resources_block, ""])

    speakers_block = _format_speakers(talk)
    if speakers_block and speakers_block != ", ".join(talk.speakers):
        lines.extend(["## Speaker Bios", speakers_block, ""])

    return "\n".join(lines).strip() + "\n"


def on_files(files, config):
    schedule = macros.get_schedule_data()
    docs_dir = Path(config["docs_dir"])
    site_dir = Path(config["site_dir"])

    generated_root = docs_dir / GENERATED_DIR_NAME
    if generated_root.exists():
        shutil.rmtree(generated_root)

    # Drop any previously generated files discovered during the initial scan
    for file in list(files):
        if file.src_path.startswith(f"{GENERATED_DIR_NAME}/"):
            files.remove(file)

    generated: Dict[str, macros.Talk] = {}
    for talk in schedule["talks"]:
        if not talk.slug:
            continue
        src_path = f"talks/{talk.slug}.md"
        manual_exists = any(file.src_path == src_path for file in files)
        manual_path = docs_dir / Path(src_path)
        if manual_exists or manual_path.exists():
            continue

        content = _build_markdown(talk)
        generated_path = generated_root / "talks" / f"{talk.slug}.md"
        generated_path.parent.mkdir(parents=True, exist_ok=True)
        generated_path.write_text(content, encoding="utf-8")

        existing = files.get_file_from_path(src_path)
        if existing:
            files.remove(existing)
        new_file = File(src_path, docs_dir, site_dir, config.get("use_directory_urls", True))
        new_file.abs_src_path = str(generated_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            files.append(new_file)
        generated[src_path] = talk

    GENERATED_TALKS.clear()
    GENERATED_TALKS.update(generated)
    return files


def on_page_read_source(page, config):
    src_path = page.file.src_path
    if src_path in GENERATED_TALKS:
        generated_root = Path(config["docs_dir"]) / GENERATED_DIR_NAME
        generated_path = generated_root / "talks" / Path(src_path).name
        return generated_path.read_text(encoding="utf-8")
    return None