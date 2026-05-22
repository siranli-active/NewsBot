from __future__ import annotations

from datetime import datetime, timedelta, timezone

from newsbot.models import NewsItem
from newsbot.selector import deduplicate, enforce_category_requirements, select_candidates, select_items


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


def test_select_candidates_recent_first_and_nodate_last() -> None:
    now = datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc)
    items = [
        _item("no-date", "u3", None),
        _item("old", "u2", 30),
        _item("recent", "u1", 2),
    ]
    out = select_candidates(items, max_items=10, now=now)
    assert [i.title for i in out] == ["recent", "old", "no-date"]


def test_select_candidates_max_items() -> None:
    now = datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc)
    items = [_item(f"n{i}", f"u{i}", i) for i in range(40)]
    out = select_candidates(items, max_items=30, now=now)
    assert len(out) == 30


def test_select_items_covers_category_quotas_and_limits_health_science_to_two_each() -> None:
    now = datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc)
    items = [
        *[_item(f"finance{i}", f"f{i}", i + 20, ["财经"]) for i in range(4)],
        *[_item(f"politics{i}", f"p{i}", i + 16, ["时政"]) for i in range(4)],
        *[_item(f"ai{i}", f"a{i}", i + 12, ["AI科技"]) for i in range(4)],
        *[_item(f"health{i}", f"h{i}", i, ["医疗卫生"]) for i in range(6)],
        *[_item(f"science{i}", f"s{i}", i + 6, ["自然科学"]) for i in range(6)],
    ]
    out = select_items(items, max_items=16, now=now)

    counts = {category: len([item for item in out if item.categories[0] == category]) for category in ["财经", "时政", "AI科技", "医疗卫生", "自然科学"]}
    assert counts["财经"] >= 4
    assert counts["时政"] >= 4
    assert counts["AI科技"] >= 4
    assert counts["医疗卫生"] == 2
    assert counts["自然科学"] == 2
    assert len(out) == 16


def test_health_quota_prioritizes_public_health_event() -> None:
    candidates = [
        _item("Drug trial", "h1", 1, ["医疗卫生"]),
        _item("Virus outbreak alert", "h2", 2, ["医疗卫生"]),
        _item("Routine hospital update", "h3", 3, ["医疗卫生"]),
    ]

    out = enforce_category_requirements(candidates, candidates, max_items=2, min_counts={"医疗卫生": 2}, exact_counts={"医疗卫生": 2})

    assert [item.title for item in out] == ["Virus outbreak alert", "Drug trial"]


def test_health_quota_includes_public_health_event_from_politics_feed() -> None:
    candidates = [
        _item("Politics", "p1", 1, ["时政"]),
        _item("伊波拉疫情", "h1", 2, ["时政"]),
    ]
    candidates[1].summary = "伊波拉病毒从动物传播至人类，引发公共卫生关注。"

    out = enforce_category_requirements(candidates, candidates, max_items=1, min_counts={"医疗卫生": 1}, exact_counts={"医疗卫生": 1})

    assert [item.title for item in out] == ["伊波拉疫情"]


def test_enforce_category_requirements_best_effort_when_category_short() -> None:
    candidates = [
        _item("finance", "f", 1, ["财经"]),
        _item("politics", "p", 2, ["时政"]),
        _item("ai", "a", 3, ["AI科技"]),
        _item("health", "h", 4, ["医疗卫生"]),
    ]

    out = enforce_category_requirements(candidates, candidates, max_items=5)

    assert [item.title for item in out] == ["finance", "politics", "ai", "health"]
