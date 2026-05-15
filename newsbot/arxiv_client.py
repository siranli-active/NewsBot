from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import feedparser

from newsbot.config import ArxivSource
from newsbot.models import NewsItem
from newsbot.rss_client import _extract_categories, _parse_published

ARXIV_API_URL = "https://export.arxiv.org/api/query"


def _normalize_text(text: object) -> str:
    return " ".join(str(text or "").split())


def _keyword_clause(keyword: str) -> str:
    escaped = keyword.replace('"', r'\"')
    return f'ti:"{escaped}" OR abs:"{escaped}"'


def build_arxiv_query(source: ArxivSource) -> str:
    keyword_query = " OR ".join(f"({_keyword_clause(keyword)})" for keyword in source.keywords)
    category_query = " OR ".join(f"cat:{category}" for category in source.categories)
    return f"({keyword_query}) AND ({category_query})"


def build_arxiv_url(source: ArxivSource) -> str:
    params = {
        "search_query": build_arxiv_query(source),
        "start": 0,
        "max_results": min(source.max_results, 5),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    return f"{ARXIV_API_URL}?{urlencode(params)}"


def _extract_authors(entry: dict) -> list[str]:
    authors = entry.get("authors")
    if not isinstance(authors, list):
        return []

    result: list[str] = []
    for author in authors:
        name = author.get("name") if isinstance(author, dict) else None
        if isinstance(name, str) and name.strip():
            result.append(name.strip())
    return result


def _has_allowed_category(item: NewsItem, allowed_categories: set[str]) -> bool:
    return any(category in allowed_categories for category in item.categories)


def fetch_arxiv_source(source: ArxivSource) -> list[NewsItem]:
    feed = feedparser.parse(build_arxiv_url(source))
    allowed_categories = set(source.categories)
    items: list[NewsItem] = []

    for entry in feed.entries:
        title = _normalize_text(entry.get("title"))
        link = str(entry.get("link", "")).strip()
        summary = _normalize_text(entry.get("summary"))
        if not title or not link:
            continue

        item = NewsItem(
            title=title,
            link=link,
            summary=summary,
            published_at=_parse_published(entry),
            categories=_extract_categories(entry),
            source=source.name,
            authors=_extract_authors(entry),
        )
        if _has_allowed_category(item, allowed_categories):
            items.append(item)
    return items


def fetch_all_arxiv(sources: list[ArxivSource]) -> list[NewsItem]:
    all_items: list[NewsItem] = []
    for source in sources:
        all_items.extend(fetch_arxiv_source(source))
    return all_items


def select_latest_arxiv(
    items: list[NewsItem],
    max_items: int = 5,
    now: datetime | None = None,
) -> list[NewsItem]:
    current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    since = current_time - timedelta(days=7)
    recent_items = [
        item
        for item in items
        if item.published_at is not None
        and since <= item.published_at.astimezone(timezone.utc) <= current_time
    ]
    return sorted(recent_items, key=lambda item: item.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[
        : min(max_items, 5)
    ]
