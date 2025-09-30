"""Schema validation helpers for schedule.yml."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ValidationError, field_validator


class Speaker(BaseModel):
    name: str
    bio: Optional[str] = None
    avatar: Optional[str] = None


SpeakerEntry = Speaker | str





class TalkModel(BaseModel):
    title: str
    slug: Optional[str] = None
    date: Optional[str | date] = None
    time: Optional[str] = None
    timezone: Optional[str] = None
    duration: Optional[int] = None
    speakers: Optional[List[SpeakerEntry]] = None
    speaker_details: Optional[List[SpeakerEntry]] = None
    tags: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    status: Optional[str] = None
    abstract: Optional[str] = None
    outline: Optional[List[str]] = None
    resources: Optional[Dict[str, str]] = None
    recording_url: Optional[str] = None
    thumbnail: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def coerce_date(cls, value: Any) -> Any:
        if isinstance(value, date):
            return value.isoformat()
        return value

    @field_validator("speaker_details", mode="before")
    @classmethod
    def normalise_speakers(cls, value: Any) -> Any:
        if value is None:
            return value
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            return value
        raise TypeError("speaker_details must be a list of dicts")


class ScheduleModel(BaseModel):
    upcoming: Optional[List[TalkModel]] = None
    past: Optional[List[TalkModel]] = None
    stats: Optional[Dict[str, Any]] = None


class ScheduleValidationError(RuntimeError):
    """Raised when schedule validation fails."""


def validate_schedule_data(payload: Any, source: Optional[Path] = None) -> ScheduleModel:
    """Validate the raw schedule payload and return the parsed model."""
    try:
        return ScheduleModel.model_validate(payload)
    except ValidationError as exc:  # pragma: no cover - exercised via call-sites
        prefix = f"{source}: " if source else ""
        raise ScheduleValidationError(f"{prefix}schedule.yml is invalid\n{exc}") from exc


def validate_schedule_file(path: Path) -> ScheduleModel:
    """Load and validate a schedule YAML file."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return validate_schedule_data(data, path)
