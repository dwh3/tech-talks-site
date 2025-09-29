from __future__ import annotations

import shutil
import warnings
from pathlib import Path
from typing import Dict

import yaml
from mkdocs.structure.files import File

import macros

GENERATED_TALKS: Dict[str, macros.Talk] = {}
GENERATED_DIR_NAME = "_generated"


def _clean_front_matter(payload: Dict[str, object]) -> Dict[str, object]:
    return {key: value for key, value in payload.items() if value not in (None, [], {}, "")}


def _format_speakers(talk: macros.Talk) -> str:
    if talk.speaker_details:
        segments = []
        for entry in talk.speaker_details:
            name = entry.get("name")
            bio = entry.get("bio")
            if name and bio:
                segments.append(f"{name} — {bio}")
            elif name:
                segments.append(str(name))
        if segments:
            return "<br/>".join(segments)
    return ", ".join(talk.speakers)


def _render_resources(talk: macros.Talk) -> str:
    items = []
    for label, href in sorted((talk.resources or {}).items()):
        if not href:
            continue
        title = label.replace("_", " ").title()
        items.append(f"- [{title}]({href})")
    if not items:
        items.append("Resources will be posted after the session.")
    return "\n".join(items)


def _render_outline(talk: macros.Talk) -> str:
    outline = talk.outline or []
    if not outline:
        return "- Session outline will be published soon."
    return "\n".join(f"- {item}" for item in outline)


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
    tz_display = talk.timezone or "UTC"
    if talk.time or talk.timezone:
        lines.append(f"**Time:** {macros._format_time(talk)} ({tz_display})")
    lines.append(f"**Speakers:** {', '.join(talk.speakers) if talk.speakers else 'TBA'}")
    topics = talk.topics or talk.tags
    if topics:
        lines.append(f"**Topics:** {', '.join(topics)}")
    lines.append("")

    lines.extend(["## Abstract", talk.abstract or "Details coming soon.", ""])
    lines.extend(["## Outline", _render_outline(talk), ""])
    lines.extend(["## Resources", _render_resources(talk), ""])

    if talk.recording_url:
        recording_body = f"[Watch the recording]({talk.recording_url})"
    else:
        recording_body = "Recording will be shared once available."
    lines.extend(["## Recording", recording_body, ""])

    speaker_bios = _format_speakers(talk)
    if talk.speaker_details and speaker_bios and speaker_bios != ", ".join(talk.speakers):
        lines.extend(["## Speaker Bios", speaker_bios, ""])

    return "\n".join(lines).strip() + "\n"


def on_files(files, config):
    schedule = macros.get_schedule_data()
    docs_dir = Path(config["docs_dir"])
    site_dir = Path(config["site_dir"])

    generated_root = docs_dir / GENERATED_DIR_NAME
    if generated_root.exists():
        shutil.rmtree(generated_root)

    # Remove any items from a previous run before regenerating
    for file in list(files):
        if file.src_path.startswith(f"{GENERATED_DIR_NAME}/"):
            files.remove(file)

    generated: Dict[str, macros.Talk] = {}
    for talk in schedule["talks"]:
        if not talk.slug:
            continue
        src_path = f"talks/{talk.slug}.md"
        manual_path = docs_dir / Path(src_path)
        if manual_path.exists():
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
