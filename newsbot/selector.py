from __future__ import annotations

from datetime import datetime, timedelta, timezone

from newsbot.config import DEFAULT_FINAL_ITEMS, MIN_FINAL_CATEGORY_COUNTS, NEWS_CATEGORIES, REQUIRED_FINAL_CATEGORY_COUNTS
from newsbot.models import NewsItem, PersonalizedNewsItem


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


def _news_item(item: NewsItem | PersonalizedNewsItem) -> NewsItem:
    return item.item if isinstance(item, PersonalizedNewsItem) else item


def _category_for_selection(item: NewsItem | PersonalizedNewsItem) -> str:
    if isinstance(item, PersonalizedNewsItem) and item.display_category in NEWS_CATEGORIES:
        return item.display_category
    base = _news_item(item)
    if _is_public_health_event(base):
        return "医疗卫生"
    for category in base.categories:
        if category in NEWS_CATEGORIES:
            return category
    return "综合"


def _has_category(item: NewsItem | PersonalizedNewsItem, category: str) -> bool:
    return _category_for_selection(item) == category


def _is_public_health_event(item: NewsItem) -> bool:
    text = f"{item.title} {item.summary}".lower()
    keywords = [
        "outbreak",
        "epidemic",
        "pandemic",
        "infection",
        "virus",
        "zoonotic",
        "public health",
        "疫情",
        "暴发",
        "爆发",
        "传染病",
        "病毒",
        "感染",
        "人畜共患",
        "公共卫生",
        "预防医学",
        "医疗",
        "卫生",
        "疾病",
        "埃博拉",
        "伊波拉",
        "新冠",
        "汉坦病毒",
        "漢坦病毒",
    ]
    return any(keyword in text for keyword in keywords)


def select_candidates(items: list[NewsItem], max_items: int = 30, now: datetime | None = None) -> list[NewsItem]:
    return prioritize_recent(deduplicate(items), now=now)[:max_items]


def enforce_category_requirements(
    ranked_items: list[NewsItem | PersonalizedNewsItem],
    candidates: list[NewsItem],
    max_items: int = DEFAULT_FINAL_ITEMS,
    exact_counts: dict[str, int] | None = None,
    min_counts: dict[str, int] | None = None,
) -> list[NewsItem | PersonalizedNewsItem]:
    exact_counts = exact_counts or REQUIRED_FINAL_CATEGORY_COUNTS
    min_counts = min_counts or MIN_FINAL_CATEGORY_COUNTS
    candidate_order = {candidate.link: index for index, candidate in enumerate(candidates)}
    ranked_by_link = {_news_item(item).link: item for item in ranked_items if _news_item(item).link in candidate_order}
    selected: list[NewsItem | PersonalizedNewsItem] = []
    selected_links: set[str] = set()

    def add(item: NewsItem | PersonalizedNewsItem) -> None:
        link = _news_item(item).link
        if link not in selected_links and len(selected) < max_items:
            selected.append(item)
            selected_links.add(link)

    def best_for_category(category: str) -> list[NewsItem | PersonalizedNewsItem]:
        ranked_matches = [item for item in ranked_items if _has_category(item, category)]
        candidate_matches = [ranked_by_link.get(item.link, item) for item in candidates if _has_category(item, category)]
        result: list[NewsItem | PersonalizedNewsItem] = []
        seen: set[str] = set()
        for item in [*ranked_matches, *candidate_matches]:
            link = _news_item(item).link
            if link not in seen:
                result.append(item)
                seen.add(link)
        if category == "医疗卫生":
            result.sort(key=lambda item: not _is_public_health_event(_news_item(item)))
        return result

    for category, count in min_counts.items():
        limit = exact_counts.get(category, count)
        for item in best_for_category(category)[:limit]:
            add(item)

    for item in ranked_items:
        if any(_has_category(item, category) and _category_count(selected, category) >= count for category, count in exact_counts.items()):
            continue
        add(item)

    for item in candidates:
        if len(selected) == max_items:
            break
        if any(_has_category(item, category) and _category_count(selected, category) >= count for category, count in exact_counts.items()):
            continue
        add(ranked_by_link.get(item.link, item))

    return selected[:max_items]


def _category_count(items: list[NewsItem | PersonalizedNewsItem], category: str) -> int:
    return sum(1 for item in items if _has_category(item, category))


def select_items(items: list[NewsItem], max_items: int = DEFAULT_FINAL_ITEMS, now: datetime | None = None) -> list[NewsItem]:
    candidates = select_candidates(items, max_items=max(len(items), max_items), now=now)
    selected = enforce_category_requirements(candidates, candidates, max_items=max_items)
    return [_news_item(item) for item in selected]
