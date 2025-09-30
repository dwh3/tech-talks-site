import re
from dataclasses import dataclass, field
from datetime import datetime, time as dtime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from lib.schedule_validation import validate_schedule_data

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"

SCHEDULE_PATHS = [
    ROOT / "data" / "schedule.yml",
    ROOT / "schedule.yml",
]

TIME_SEP = "\u2013"


@dataclass
class Talk:
    title: str
    date: Optional[str] = None
    time: Optional[str] = None
    timezone: Optional[str] = None
    duration: Optional[int] = None
    speakers: List[str] = field(default_factory=list)
    speaker_details: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    slug: Optional[str] = None
    link: Optional[str] = None
    thumbnail: Optional[str] = None
    abstract: Optional[str] = None
    outline: List[str] = field(default_factory=list)
    resources: Dict[str, str] = field(default_factory=dict)
    recording_url: Optional[str] = None
    status: Optional[str] = None

    dt: Optional[datetime] = None
    iso_start: Optional[str] = None
    date_str: Optional[str] = None
    time_str: Optional[str] = None


def _safe_zone(tz: Optional[str]):
    try:
        from zoneinfo import ZoneInfo
    except Exception:  # pragma: no cover
        return timezone.utc

    try:
        return ZoneInfo(tz) if tz else ZoneInfo("UTC")
    except Exception:
        return ZoneInfo("UTC")


def _parse_time_window(raw: Optional[str]) -> dtime:
    if not raw:
        return dtime(0, 0)
    text = str(raw).strip()
    if TIME_SEP in text:
        text = text.split(TIME_SEP, 1)[0]
    elif "-" in text:
        text = text.split("-", 1)[0]
    hours, minutes = (text.split(":") + ["0"])[:2]
    return dtime(int(hours), int(minutes))


def _mk_dt(date_str: Optional[str], time_str: Optional[str], tz_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        year, month, day = (int(part) for part in str(date_str).split("-"))
    except Exception:
        return None
    parsed_time = _parse_time_window(time_str)
    try:
        tz = _safe_zone(tz_str)
    except Exception:
        tz = None
    return datetime(year, month, day, parsed_time.hour, parsed_time.minute, tzinfo=tz)


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _normalise_speakers(raw: Any) -> (List[str], List[Dict[str, Any]]):
    names: List[str] = []
    details: List[Dict[str, Any]] = []
    if not raw:
        return names, details
    items = raw if isinstance(raw, list) else [raw]
    for entry in items:
        if isinstance(entry, dict):
            details.append(entry)
            name = entry.get("name")
            if name:
                names.append(str(name))
        else:
            names.append(str(entry))
    return names, details


def _normalise_outline(raw: Any) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw if item]
    if isinstance(raw, str):
        return [part.strip() for part in raw.splitlines() if part.strip()]
    return []


def _collect_resources(item: Dict[str, Any]) -> Dict[str, str]:
    resources: Dict[str, str] = {}
    block = item.get("resources")
    if isinstance(block, dict):
        for key, value in block.items():
            if value:
                resources[key] = str(value)
    legacy_keys = {
        "slides_url": "slides",
        "notebook_url": "notebook",
        "repo": "repo",
        "repo_url": "repo",
    }
    for key, label in legacy_keys.items():
        value = item.get(key)
        if value:
            resources[label] = str(value)
    return resources


def _coerce_tags(raw: Any) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw if item]
    if isinstance(raw, str):
        return [part.strip() for part in raw.split(",") if part.strip()]
    return []


def _read_schedule() -> List[Talk]:
    talks: List[Talk] = []
    for schedule_path in SCHEDULE_PATHS:
        if not schedule_path.exists():
            continue
        raw_data = _load_yaml(schedule_path)
        if raw_data is None:
            continue
        validate_schedule_data(raw_data, schedule_path)
        data = raw_data or {}
        sections: Dict[str, List[Dict[str, Any]]] = {}
        if isinstance(data, list):
            sections = {"mixed": data}
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    sections[key] = value
        for section in ("upcoming", "past", "mixed"):
            for item in sections.get(section, []):
                if not isinstance(item, dict):
                    continue
                names, details = _normalise_speakers(item.get("speakers") or item.get("speaker"))
                talk = Talk(
                    title=str(item.get("title") or ""),
                    date=str(item.get("date")) if item.get("date") else None,
                    time=str(item.get("time")) if item.get("time") else None,
                    timezone=item.get("timezone"),
                    duration=item.get("duration"),
                    speakers=names,
                    speaker_details=details,
                    tags=_coerce_tags(item.get("tags")),
                    topics=_coerce_tags(item.get("topics")),
                    slug=item.get("slug"),
                    thumbnail=item.get("thumbnail"),
                    abstract=item.get("abstract"),
                    outline=_normalise_outline(item.get("outline")),
                    resources=_collect_resources(item),
                    recording_url=item.get("recording_url"),
                    status=item.get("status"),
                )
                if talk.slug and not talk.link:
                    talk.link = f"talks/{talk.slug}.md"
                elif item.get("link"):
                    talk.link = str(item.get("link"))
                talks.append(talk)
        break
    return talks


def _front_matter(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except Exception:
        return {}


def _read_talk_pages() -> List[Talk]:
    talks: List[Talk] = []
    talks_dir = DOCS / "talks"
    if not talks_dir.exists():
        return talks
    for md_file in talks_dir.glob("*.md"):
        fm = _front_matter(md_file)
        if not fm:
            continue
        names, details = _normalise_speakers(fm.get("speakers") or fm.get("speaker"))
        talk = Talk(
            title=str(fm.get("title") or md_file.stem.replace("-", " ").title()),
            date=str(fm.get("date")) if fm.get("date") else None,
            time=fm.get("time"),
            timezone=fm.get("timezone"),
            duration=fm.get("duration"),
            speakers=names,
            speaker_details=details,
            tags=_coerce_tags(fm.get("tags")),
            topics=_coerce_tags(fm.get("topics")),
            slug=md_file.stem,
            link=str(md_file.relative_to(DOCS)).replace("\\", "/"),
            thumbnail=fm.get("thumbnail"),
            abstract=fm.get("abstract"),
            outline=_normalise_outline(fm.get("outline")),
            resources=_collect_resources(fm),
            recording_url=fm.get("recording_url"),
            status=fm.get("status"),
        )
        talks.append(talk)
    return talks


def _merge_schedule_and_pages(schedule_talks: List[Talk], page_talks: List[Talk]) -> List[Talk]:
    by_slug: Dict[str, Talk] = {talk.slug: talk for talk in page_talks if talk.slug}
    merged: List[Talk] = []
    seen: set = set()
    for talk in schedule_talks:
        if talk.slug and talk.slug in by_slug:
            page_talk = by_slug[talk.slug]
            combined = Talk(
                title=page_talk.title or talk.title,
                date=page_talk.date or talk.date,
                time=page_talk.time or talk.time,
                timezone=page_talk.timezone or talk.timezone,
                duration=page_talk.duration or talk.duration,
                speakers=page_talk.speakers or talk.speakers,
                speaker_details=page_talk.speaker_details or talk.speaker_details,
                tags=page_talk.tags or talk.tags,
                topics=page_talk.topics or talk.topics,
                slug=talk.slug,
                link=page_talk.link or talk.link,
                thumbnail=page_talk.thumbnail or talk.thumbnail,
                abstract=page_talk.abstract or talk.abstract,
                outline=page_talk.outline or talk.outline,
                resources=page_talk.resources or talk.resources,
                recording_url=page_talk.recording_url or talk.recording_url,
                status=page_talk.status or talk.status,
            )
            merged.append(combined)
            seen.add(talk.slug)
        else:
            merged.append(talk)
            if talk.slug:
                seen.add(talk.slug)
    for talk in page_talks:
        if talk.slug and talk.slug in seen:
            continue
        merged.append(talk)
    return merged


def _decorate(talk: Talk) -> Talk:
    talk.dt = _mk_dt(talk.date, talk.time, talk.timezone)
    talk.iso_start = talk.dt.isoformat() if talk.dt else None
    talk.date_str = talk.date or (talk.dt.strftime("%Y-%m-%d") if talk.dt else None)
    talk.time_str = talk.time
    if talk.slug and not talk.link:
        talk.link = f"talks/{talk.slug}.md"
    return talk


def _format_date(talk: Talk) -> str:
    if talk.dt:
        return talk.dt.strftime("%B %d, %Y")
    return talk.date or "TBA"


def _format_time(talk: Talk) -> str:
    if talk.dt:
        return talk.dt.strftime("%H:%M")
    return talk.time or "TBA"


def _build() -> Dict[str, Any]:
    schedule_talks = _read_schedule()
    page_talks = _read_talk_pages()
    talks = [_decorate(talk) for talk in _merge_schedule_and_pages(schedule_talks, page_talks)]

    now = datetime.now(timezone.utc)

    def future_key(item: Talk) -> datetime:
        return item.dt or datetime.max.replace(tzinfo=timezone.utc)

    def past_key(item: Talk) -> datetime:
        return item.dt or datetime.min.replace(tzinfo=timezone.utc)

    upcoming = sorted([talk for talk in talks if talk.dt and talk.dt >= now], key=future_key)
    past = sorted([talk for talk in talks if talk.dt and talk.dt < now], key=past_key, reverse=True)

    next_talk = upcoming[0] if upcoming else (sorted(talks, key=future_key)[0] if talks else None)

    delivered = len(past)
    speaker_names = {name for talk in upcoming for name in talk.speakers if name}
    tag_counts: Dict[str, int] = {}
    for talk in talks:
        for bucket in (talk.tags or []):
            tag_counts[bucket] = tag_counts.get(bucket, 0) + 1
        for topic in talk.topics or []:
            tag_counts[topic] = tag_counts.get(topic, 0) + 1
    top_tag = max(tag_counts, key=tag_counts.get) if tag_counts else "N/A"

    return {
        "talks": talks,
        "upcoming": upcoming,
        "past": past,
        "next_talk": next_talk,
        "recent": past[:6],
        "stats": {
            "delivered": delivered,
            "upcoming_speakers": len(speaker_names),
            "top_tag": top_tag,
        },
    }


def get_schedule_data() -> Dict[str, Any]:
    return _build()


def get_talk_by_slug(slug: str) -> Optional[Talk]:
    for talk in _build()["talks"]:
        if talk.slug == slug:
            return talk
    return None


def define_env(env):
    @env.macro
    def dashboard_next_talk():
        data = _build()
        talk = data.get("next_talk")
        if not talk:
            return '<div class="admonition info"><p>No upcoming talk is scheduled.</p></div>'
        speakers = ", ".join(talk.speakers) if talk.speakers else "TBA"
        topics = ", ".join(talk.topics or talk.tags or []) if (talk.topics or talk.tags) else "N/A"
        link = talk.link or "#"
        iso = talk.iso_start or ""
        date_line = talk.date_str or "TBA"
        time_line = f" • {talk.time_str}" if talk.time_str else ""
        return f"""
<section class="dashboard next-talk">
  <div class="card">
    <div class="card__body">
      <h2>Next Talk</h2>
      <h3 class="talk-title"><a href="{link}">{talk.title}</a></h3>
      <p class="muted">{date_line}{time_line}</p>
      <p><strong>Speaker:</strong> {speakers}</p>
      <p><strong>Topics:</strong> {topics}</p>
      <div class="countdown" data-start="{iso}">
        <strong>Starts in:</strong> <span class="cd-out">--</span>
      </div>
    </div>
  </div>
</section>
"""

    @env.macro
    def dashboard_quick_stats():
        stats = _build()["stats"]
        return f"""
<section class="dashboard quick-stats">
  <div class="stats-grid">
    <div class="stat"><div class="num">{stats['delivered']}</div><div class="label">Talks delivered</div></div>
    <div class="stat"><div class="num">{stats['upcoming_speakers']}</div><div class="label">Upcoming speakers</div></div>
    <div class="stat"><div class="num">{stats['top_tag']}</div><div class="label">Top topic</div></div>
  </div>
</section>
"""

    @env.macro
    def dashboard_recent_talks(count: int = 4):
        recent = _build()["recent"][: int(count)]
        if not recent:
            return ""
        cards: List[str] = []
        for talk in recent:
            thumb = talk.thumbnail or "images/logo.svg"
            link = talk.link or "#"
            date_line = _format_date(talk)
            cards.append(
                f"""
  <article class="card talk-card">
    <a class="talk-link" href="{link}">
      <div class="thumb"><img src="/{thumb}" alt="thumbnail"></div>
      <div class="meta">
        <h4 class="title">{talk.title}</h4>
        <div class="date muted">{date_line}</div>
      </div>
    </a>
  </article>
"""
            )
        return f"""
<section class="dashboard recent-talks">
  <div class="section-title"><h2>Recent Talks</h2></div>
  <div class="carousel" tabindex="0" aria-label="Recent talks">
    {''.join(cards)}
  </div>
</section>
"""

    @env.macro
    def generate_schedule():
        data = _build()
        upcoming = data["upcoming"]
        past = data["past"]
        lines: List[str] = ["# Upcoming Sessions", ""]
        if not upcoming:
            lines.append("No upcoming sessions are scheduled right now. Check back soon!")
        else:
            for talk in upcoming:
                lines.append(f"## {talk.title}")
                lines.append("")
                lines.append(f"- **Date:** {_format_date(talk)}")
                if talk.time or talk.timezone:
                    tz_display = talk.timezone or "UTC"
                    lines.append(f"- **Time:** {_format_time(talk)} ({tz_display})")
                if talk.speakers:
                    lines.append(f"- **Speakers:** {', '.join(talk.speakers)}")
                topics = talk.topics or talk.tags
                if topics:
                    lines.append(f"- **Topics:** {', '.join(topics)}")
                if talk.status:
                    lines.append(f"- **Status:** {talk.status}")
                if talk.link:
                    lines.append(f"- [View details]({talk.link})")
                lines.append("")
        lines.extend(["# Past Sessions", ""])
        if not past:
            lines.append("No sessions delivered yet.")
        else:
            for talk in past:
                lines.append(f"- **{_format_date(talk)} — {talk.title}**")
                extras: List[str] = []
                if talk.speakers:
                    extras.append("Speakers: " + ", ".join(talk.speakers))
                if talk.link:
                    extras.append(f"[Resources]({talk.link})")
                if extras:
                    lines.append("  - " + " | ".join(extras))
        return "\n".join(lines)

    @env.macro
    def generate_past_index():
        data = _build()
        past = data["past"]
        lines: List[str] = ["# Past Talks", ""]
        if not past:
            lines.append("No sessions delivered yet.")
        else:
            for talk in past:
                date_label = _format_date(talk)
                heading = f"{date_label} — {talk.title}"
                link = talk.link or ""
                if link.startswith("talks/"):
                    link = link.split("/", 1)[1]
                if link:
                    lines.append(f"- **[{heading}]({link})**")
                else:
                    lines.append(f"- **{heading}**")
                details: List[str] = []
                if talk.speakers:
                    details.append("Speakers: " + ", ".join(talk.speakers))
                topics = talk.topics or talk.tags
                if topics:
                    details.append("Topics: " + ", ".join(topics))
                if talk.resources:
                    details.append("Resources available")
                if talk.recording_url:
                    details.append(f"[Recording]({talk.recording_url})")
                if details:
                    lines.append("  - " + " | ".join(details))
        return "\n".join(lines)

    return env
