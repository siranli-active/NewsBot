from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    published_at: datetime | None
    categories: list[str]
    source: str
    authors: list[str] | None = None


@dataclass
class PersonalizedNewsItem:
    item: NewsItem
    translated_title: str | None = None
    translated_summary: str | None = None
    importance_reason: str | None = None
    display_category: str | None = None


@dataclass
class PersonalizedBriefing:
    items: list[PersonalizedNewsItem]
    focus_directions: dict[str, list[str]]
