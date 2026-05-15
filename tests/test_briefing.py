from __future__ import annotations

from datetime import datetime, timezone

from newsbot.briefing import FALLBACK_SUMMARY, build_briefing
from newsbot.models import NewsItem


def _item(title: str, summary: str, categories: list[str]) -> NewsItem:
    return NewsItem(
        title=title,
        link="https://example.com",
        summary=summary,
        published_at=datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc),
        categories=categories,
        source="src",
    )


def test_briefing_focus_and_top3_titles() -> None:
    items = [
        _item("A", "句子一。句子二。句子三。", ["Tech"]),
        _item("B", "Only one sentence", ["Tech"]),
        _item("C", "", ["World"]),
    ]
    text = build_briefing(items)
    assert "重点方向：Tech" in text
    assert "- A" in text and "- B" in text and "- C" in text
    assert FALLBACK_SUMMARY in text


def test_briefing_test_mode_prefix() -> None:
    items = [_item("A", "Hello world.", ["Tech"])]
    text = build_briefing(items, test_mode=True)
    assert "【测试】中文早间新闻简报" in text
    assert "1. 【测试】A" in text


def test_briefing_arxiv_section() -> None:
    paper = NewsItem(
        title="Active matter paper",
        link="https://arxiv.org/abs/2605.00001",
        summary="A" * 301,
        published_at=datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc),
        categories=["cond-mat.soft"],
        source="arXiv Active Matter",
        authors=["Author One", "Author Two", "Author Three"],
    )

    text = build_briefing([], arxiv_papers=[paper])

    assert "📚 每周 arXiv / Active Matter 论文" in text
    assert "1. Active matter paper" in text
    assert "作者：Author One, Author Two" in text
    assert "Author Three" not in text
    assert f"摘要：{'A' * 300}" in text
    assert "https://arxiv.org/abs/2605.00001" in text


def test_briefing_arxiv_empty_state() -> None:
    text = build_briefing([], arxiv_papers=[])
    assert "过去一周内没有检索到 active matter 相关 arXiv 论文。" in text
