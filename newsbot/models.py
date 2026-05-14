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
