from __future__ import annotations

from datetime import datetime, timezone
from time import struct_time

import feedparser
from dateutil import parser as date_parser

from newsbot.config import Source
from newsbot.models import NewsItem


def _parse_published(entry: dict) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if isinstance(parsed, struct_time):
        return datetime(*parsed[:6], tzinfo=timezone.utc)

    raw = entry.get("published") or entry.get("updated")
    if isinstance(raw, str) and raw.strip():
        try:
            dt = date_parser.parse(raw)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, OverflowError):
            return None
    return None


def _extract_categories(entry: dict) -> list[str]:
    tags = entry.get("tags")
    if not isinstance(tags, list):
        return []
    result: list[str] = []
    for t in tags:
        term = t.get("term") if isinstance(t, dict) else None
        if isinstance(term, str) and term.strip():
            result.append(term.strip())
    return result


def fetch_source(source: Source) -> list[NewsItem]:
    feed = feedparser.parse(source.url)
    items: list[NewsItem] = []
    for entry in feed.entries:
        title = str(entry.get("title", "")).strip()
        link = str(entry.get("link", "")).strip()
        summary = str(entry.get("summary") or entry.get("description") or "").strip()
        if not title or not link:
            continue
        feed_categories = _extract_categories(entry)
        categories = [source.category, *[cat for cat in feed_categories if cat != source.category]]
        items.append(
            NewsItem(
                title=title,
                link=link,
                summary=summary,
                published_at=_parse_published(entry),
                categories=categories,
                source=source.name,
            )
        )
    return items


def fetch_all(sources: list[Source]) -> list[NewsItem]:
    all_items: list[NewsItem] = []
    for source in sources:
        all_items.extend(fetch_source(source))
    return all_items
