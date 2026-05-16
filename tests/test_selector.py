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


def test_select_limits_health_and_science_to_four_combined() -> None:
    now = datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc)
    items = [
        *[_item(f"health{i}", f"h{i}", i, ["医疗卫生"]) for i in range(6)],
        *[_item(f"science{i}", f"s{i}", i + 6, ["自然科学"]) for i in range(6)],
        *[_item(f"finance{i}", f"f{i}", i + 12, ["财经"]) for i in range(6)],
    ]
    out = select_items(items, max_items=18, now=now)

    limited_count = len([item for item in out if item.categories[0] in {"医疗卫生", "自然科学"}])
    assert limited_count == 4
    assert len([item for item in out if item.categories[0] == "财经"]) == 6
    assert len(out) == 10
