from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlparse
from unittest.mock import patch

from newsbot.arxiv_client import build_arxiv_url, fetch_arxiv_source, select_latest_arxiv
from newsbot.config import ArxivSource
from newsbot.models import NewsItem


def _source(max_results: int = 10) -> ArxivSource:
    return ArxivSource(
        name="arXiv Active Matter",
        keywords=["active matter", "AOUP"],
        categories=["cond-mat.soft", "physics.bio-ph"],
        max_results=max_results,
    )


def test_build_arxiv_url() -> None:
    url = build_arxiv_url(_source())
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    query = unquote(params["search_query"][0])

    assert parsed.scheme == "https"
    assert parsed.netloc == "export.arxiv.org"
    assert parsed.path == "/api/query"
    assert params["max_results"] == ["5"]
    assert params["sortBy"] == ["submittedDate"]
    assert params["sortOrder"] == ["descending"]
    assert 'ti:"active matter"' in query
    assert 'abs:"AOUP"' in query
    assert "cat:cond-mat.soft" in query
    assert "cat:physics.bio-ph" in query


@patch("newsbot.arxiv_client.feedparser.parse")
def test_fetch_arxiv_source_parses_and_filters(mock_parse) -> None:
    mock_parse.return_value = SimpleNamespace(
        entries=[
            {
                "title": " Active\nMatter Paper ",
                "link": "https://arxiv.org/abs/2605.00001",
                "summary": " Abstract\ntext ",
                "published": "2026-05-14T08:00:00Z",
                "tags": [{"term": "cond-mat.soft"}],
                "authors": [{"name": "Author One"}, {"name": "Author Two"}],
            },
            {
                "title": "Wrong category",
                "link": "https://arxiv.org/abs/2605.00002",
                "summary": "Abstract",
                "published": "2026-05-14T09:00:00Z",
                "tags": [{"term": "cs.AI"}],
                "authors": [{"name": "Author Three"}],
            },
        ]
    )

    items = fetch_arxiv_source(_source())

    assert len(items) == 1
    assert items[0].title == "Active Matter Paper"
    assert items[0].summary == "Abstract text"
    assert items[0].authors == ["Author One", "Author Two"]
    assert items[0].published_at == datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc)


def test_select_latest_arxiv_returns_past_week_newest_five() -> None:
    now = datetime(2026, 5, 15, 12, tzinfo=timezone.utc)
    items = [
        NewsItem(
            title=f"Paper {days_ago}",
            link=f"https://arxiv.org/abs/{days_ago}",
            summary="Abstract",
            published_at=now - timedelta(days=days_ago),
            categories=["cond-mat.soft"],
            source="arXiv",
        )
        for days_ago in range(6)
    ]
    items.append(
        NewsItem(
            title="Old Paper",
            link="https://arxiv.org/abs/old",
            summary="Abstract",
            published_at=now - timedelta(days=8),
            categories=["cond-mat.soft"],
            source="arXiv",
        )
    )

    selected = select_latest_arxiv(items, now=now)

    assert [item.title for item in selected] == ["Paper 0", "Paper 1", "Paper 2", "Paper 3", "Paper 4"]


def test_select_latest_arxiv_returns_empty_when_no_past_week_papers() -> None:
    now = datetime(2026, 5, 15, 12, tzinfo=timezone.utc)
    items = [
        NewsItem(
            title="Old Paper",
            link="https://arxiv.org/abs/old",
            summary="Abstract",
            published_at=now - timedelta(days=8),
            categories=["cond-mat.soft"],
            source="arXiv",
        )
    ]

    selected = select_latest_arxiv(items, now=now)

    assert selected == []
