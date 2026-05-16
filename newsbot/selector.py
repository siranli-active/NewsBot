from __future__ import annotations

from datetime import datetime, timedelta, timezone

from newsbot.config import COMBINED_CATEGORY_LIMIT, COMBINED_LIMITED_CATEGORIES
from newsbot.models import NewsItem


def deduplicate(items: list[NewsItem]) -> list[NewsItem]:
    seen: set[tuple[str, str]] = set()
    result: list[NewsItem] = []
    for item in items:
        key = (item.title.strip().lower(), item.link.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def prioritize_recent(items: list[NewsItem], now: datetime | None = None) -> list[NewsItem]:
    current = now or datetime.now(timezone.utc)
    cutoff = current - timedelta(hours=24)

    recent: list[NewsItem] = []
    older: list[NewsItem] = []
    nodate: list[NewsItem] = []

    for item in items:
        if item.published_at is None:
            nodate.append(item)
        elif item.published_at >= cutoff:
            recent.append(item)
        else:
            older.append(item)

    recent.sort(key=lambda x: x.published_at, reverse=True)
    older.sort(key=lambda x: x.published_at, reverse=True)
    return recent + older + nodate


def _is_combined_limited_category(item: NewsItem) -> bool:
    return any(category in COMBINED_LIMITED_CATEGORIES for category in item.categories)


def select_items(items: list[NewsItem], max_items: int = 15, now: datetime | None = None) -> list[NewsItem]:
    unique = deduplicate(items)
    ordered = prioritize_recent(unique, now=now)
    selected: list[NewsItem] = []
    combined_limited_count = 0

    for item in ordered:
        is_combined_limited = _is_combined_limited_category(item)
        if is_combined_limited:
            if combined_limited_count >= COMBINED_CATEGORY_LIMIT:
                continue
            combined_limited_count += 1

        selected.append(item)
        if len(selected) == max_items:
            break

    return selected
