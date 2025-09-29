import os, re, json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, time as dtime, timezone
from zoneinfo import ZoneInfo
import yaml
from functools import lru_cache
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

SCHEDULE_PATHS = [
    ROOT / "data" / "schedule.yml",
    ROOT / "schedule.yml",
]

TIME_SEP = "–"  # en dash used in sample front matter; also support hyphen fallback


@dataclass
class Talk:
    title: str
    date: Optional[str] = None           # YYYY-MM-DD
    time: Optional[str] = None           # e.g., "12:00–13:00" or "12:00"
    timezone: Optional[str] = None       # e.g., "America/New_York"
    speakers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    link: Optional[str] = None           # relative url to markdown page
    thumbnail: Optional[str] = None
    slug: Optional[str] = None

    # computed
    dt: Optional[datetime] = None        # start datetime (tz-aware)
    iso_start: Optional[str] = None
    date_str: Optional[str] = None
    time_str: Optional[str] = None


def _safe_zone(tz: Optional[str]) -> ZoneInfo:
    try:
        return ZoneInfo(tz) if tz else ZoneInfo("UTC")
    except Exception:
        return ZoneInfo("UTC")


def _parse_time_window(s: str) -> dtime:
    """
    Returns the *start* time from a string like "12:00–13:00" or "12:00-13:00" or "12:00".
    """
    if not s:
        return dtime(0, 0)
    s = s.strip()
    if TIME_SEP in s:
        s = s.split(TIME_SEP, 1)[0]
    elif "-" in s:
        s = s.split("-", 1)[0]
    h, m = (s.split(":") + ["0"])[:2]
    return dtime(int(h), int(m))


def _mk_dt(date_str: Optional[str], time_str: Optional[str], tz_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    t = _parse_time_window(time_str) if time_str else dtime(0, 0)
    try:
        y, m, d = [int(x) for x in date_str.split("-")]
        tz = _safe_zone(tz_str)
        return datetime(y, m, d, t.hour, t.minute, tzinfo=tz)
    except Exception:
        return None


def _front_matter(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def _read_schedule() -> List[Talk]:
    entries: List[Talk] = []
    for p in SCHEDULE_PATHS:
        if p.exists():
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            # Expect either {'upcoming': [..], 'past': [..]} or a flat list
            for section in ("upcoming", "past"):
                for item in data.get(section, []) or []:
                    entries.append(Talk(
                        title=item.get("title") or "",
                        date=str(item.get("date")) if item.get("date") else None,
                        time=item.get("time"),
                        timezone=item.get("timezone"),
                        speakers=item.get("speakers") or item.get("speaker") or [],
                        tags=item.get("tags") or [],
                        topics=item.get("topics") or [],
                        slug=item.get("slug"),
                        link=(f"talks/{item.get('slug')}.md" if item.get("slug") else None),
                    ))
            # If it was a flat list
            if not entries and isinstance(data, list):
                for item in data:
                    entries.append(Talk(
                        title=item.get("title") or "",
                        date=str(item.get("date")) if item.get("date") else None,
                        time=item.get("time"),
                        timezone=item.get("timezone"),
                        speakers=item.get("speakers") or [],
                        tags=item.get("tags") or [],
                        topics=item.get("topics") or [],
                        slug=item.get("slug"),
                        link=(f"talks/{item.get('slug')}.md" if item.get("slug") else None),
                    ))
            break
    return entries


def _read_talk_pages() -> List[Talk]:
    talks: List[Talk] = []
    talks_dir = DOCS / "talks"
    if not talks_dir.exists():
        return talks
    for md in talks_dir.glob("*.md"):
        fm = _front_matter(md)
        if not fm:
            continue
        speakers = []
        if isinstance(fm.get("speaker"), list):  # your sample uses 'speaker' list of dicts
            for s in fm["speaker"]:
                name = s.get("name")
                title = s.get("title")
                org = s.get("org")
                parts = [p for p in [name, title, org] if p]
                speakers.append(", ".join(parts) if parts else name)
        elif isinstance(fm.get("speakers"), list):
            speakers = [str(x) for x in fm["speakers"]]

        talk = Talk(
            title=fm.get("title") or md.stem.replace("-", " ").title(),
            date=str(fm.get("date")) if fm.get("date") else None,
            time=fm.get("time"),
            timezone=fm.get("timezone"),
            speakers=speakers,
            tags=fm.get("tags") or [],
            topics=fm.get("topics") or [],
            link=str(md.relative_to(DOCS)).replace("\\", "/"),
            slug=md.stem,
            thumbnail=fm.get("thumbnail"),
        )
        talks.append(talk)
    return talks


def _merge_schedule_and_pages(sched: List[Talk], pages: List[Talk]) -> List[Talk]:
    by_slug: Dict[str, Talk] = {t.slug: t for t in pages if t.slug}
    out: List[Talk] = []
    if not sched:
        return pages
    for s in sched:
        if s.slug and s.slug in by_slug:
            p = by_slug[s.slug]
            # prefer page details if available; fall back to schedule values
            merged = Talk(
                title=p.title or s.title,
                date=p.date or s.date,
                time=p.time or s.time,
                timezone=p.timezone or s.timezone,
                speakers=p.speakers or s.speakers,
                tags=(p.tags or s.tags),
                topics=(p.topics or s.topics),
                link=p.link or s.link,
                slug=s.slug,
                thumbnail=p.thumbnail,
            )
            out.append(merged)
        else:
            out.append(s)
    # add any page-only talks not in schedule (likely past)
    sched_slugs = {t.slug for t in sched if t.slug}
    out.extend([t for t in pages if t.slug not in sched_slugs])
    return out


def _decorate(t: Talk) -> Talk:
    t.dt = _mk_dt(t.date, t.time, t.timezone)
    t.iso_start = t.dt.isoformat() if t.dt else None
    t.date_str = t.date
    t.time_str = t.time
    return t


@lru_cache(maxsize=1)
def _build() -> Dict[str, Any]:
    sched = _read_schedule()
    pages = _read_talk_pages()
    talks = [_decorate(t) for t in _merge_schedule_and_pages(sched, pages)]

    now = datetime.now(timezone.utc)
    upcoming = [t for t in talks if t.dt and t.dt >= now]
    past = sorted([t for t in talks if t.dt and t.dt < now], key=lambda x: x.dt, reverse=True)

    next_talk = sorted(upcoming, key=lambda x: x.dt)[0] if upcoming else (sorted([t for t in talks if t.dt], key=lambda x: x.dt)[0] if talks else None)

    # stats
    delivered = len(past)
    upcoming_speakers = len({s for t in upcoming for s in t.speakers})
    tag_counts: Dict[str, int] = {}
    for t in talks:
        for tag in t.tags or []:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    top_tag = max(tag_counts, key=tag_counts.get) if tag_counts else "–"

    return {
        "talks": talks,
        "next_talk": next_talk,
        "recent": past[:6],  # keep a small window; we'll slice further in the macro
        "stats": {
            "delivered": delivered,
            "upcoming_speakers": upcoming_speakers,
            "top_tag": top_tag,
        },
    }


def define_env(env):
    """MkDocs Macros entry point."""
    @env.macro
    def dashboard_next_talk():
        data = _build()
        t = data.get("next_talk")
        if not t:
            return '<div class="admonition info"><p>No upcoming talk is scheduled.</p></div>'

        speakers = ", ".join(t.speakers) if t.speakers else "TBA"
        topics = ", ".join(t.topics or t.tags or []) if (t.topics or t.tags) else "–"
        link = t.link or "#"
        iso = t.iso_start or ""
        date_line = t.date_str or "TBA"
        time_line = f" • {t.time_str}" if t.time_str else ""

        return f"""
<section class="dashboard next-talk">
  <div class="card">
    <div class="card__body">
      <h2>Next Talk</h2>
      <h3 class="talk-title"><a href="{link}">{t.title}</a></h3>
      <p class="muted">{date_line}{time_line}</p>
      <p><strong>Speaker:</strong> {speakers}</p>
      <p><strong>Topics:</strong> {topics}</p>
      <div class="countdown" data-start="{iso}">
        <strong>Starts in:</strong> <span class="cd-out">—</span>
      </div>
    </div>
  </div>
</section>
"""

    @env.macro
    def dashboard_quick_stats():
        s = _build()["stats"]
        return f"""
<section class="dashboard quick-stats">
  <div class="stats-grid">
    <div class="stat"><div class="num">{s['delivered']}</div><div class="label">Talks delivered</div></div>
    <div class="stat"><div class="num">{s['upcoming_speakers']}</div><div class="label">Upcoming speakers</div></div>
    <div class="stat"><div class="num">{s['top_tag']}</div><div class="label">Top topic</div></div>
  </div>
</section>
"""

    @env.macro
    def dashboard_recent_talks(n: int = 4):
        recent = _build()["recent"][:int(n)]
        if not recent:
            return ""
        cards = []
        for t in recent:
            thumb = t.thumbnail or "images/logo.svg"  # fallback
            link = t.link or "#"
            date_line = t.date_str or ""
            cards.append(f"""
  <article class="card talk-card">
    <a class="talk-link" href="{link}">
      <div class="thumb"><img src="/{thumb}" alt="thumbnail"></div>
      <div class="meta">
        <h4 class="title">{t.title}</h4>
        <div class="date muted">{date_line}</div>
      </div>
    </a>
  </article>
""")
        return f"""
<section class="dashboard recent-talks">
  <div class="section-title"><h2>Recent Talks</h2></div>
  <div class="carousel" tabindex="0" aria-label="Recent talks">
    {''.join(cards)}
  </div>
</section>
"""
