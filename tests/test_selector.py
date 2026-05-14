from __future__ import annotations

from datetime import datetime, timedelta, timezone

from newsbot.models import NewsItem
from newsbot.selector import deduplicate, select_items


def _item(title: str, link: str, hours_ago: int | None, categories: list[str] | None = None) -> NewsItem:
    now = datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc)
    published = None if hours_ago is None else now - timedelta(hours=hours_ago)
    return NewsItem(
        title=title,
        link=link,
        summary="summary",
        published_at=published,
        categories=categories or [],
        source="src",
    )


def test_deduplicate_by_title_and_link() -> None:
    items = [
        _item("A", "u1", 1),
        _item("A", "u1", 2),
        _item("A", "u2", 3),
    ]
    out = deduplicate(items)
    assert len(out) == 2


def test_select_recent_first_and_nodate_last() -> None:
    now = datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc)
    items = [
        _item("no-date", "u3", None),
        _item("old", "u2", 30),
        _item("recent", "u1", 2),
    ]
    out = select_items(items, max_items=10, now=now)
    assert [i.title for i in out] == ["recent", "old", "no-date"]


def test_select_max_items() -> None:
    now = datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc)
    items = [_item(f"n{i}", f"u{i}", i) for i in range(10)]
    out = select_items(items, max_items=3, now=now)
    assert len(out) == 3
