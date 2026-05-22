from __future__ import annotations

from datetime import datetime, timezone

from newsbot.briefing import FALLBACK_SUMMARY, build_briefing
from newsbot.models import NewsItem, PersonalizedNewsItem


def _item(title: str, summary: str, categories: list[str]) -> NewsItem:
    return NewsItem(
        title=title,
        link="https://example.com",
        summary=summary,
        published_at=datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc),
        categories=categories,
        source="src",
    )


def test_briefing_focus_and_sections() -> None:
    items = [
        _item("A", "句子一。句子二。句子三。", ["AI科技"]),
        _item("B", "Only one sentence", ["AI科技"]),
        _item("C", "", ["财经"]),
    ]
    text = build_briefing(items)
    assert "重点方向：" in text
    assert "重点关注：" not in text
    assert "- 财经：" in text
    assert "- AI科技：" in text
    assert "💰 财经" in text
    assert "🤖 AI科技" in text
    assert "🏛️ 时政" not in text
    assert "1. C" in text
    assert "2. A" in text
    assert "3. B" in text
    assert FALLBACK_SUMMARY in text


def test_briefing_personalized_fields() -> None:
    item = PersonalizedNewsItem(
        item=_item("English title", "English summary.", ["AI科技", "医疗卫生"]),
        translated_title="中文标题",
        translated_summary="中文摘要。",
        importance_reason="与持仓相关",
        display_category="医疗卫生",
    )

    text = build_briefing(
        [item],
        focus_directions={"医疗卫生": ["基于画像的医疗方向"]},
    )

    assert "- 医疗卫生：基于画像的医疗方向" in text
    assert "重点关注：" not in text
    assert "🏥 医疗卫生" in text
    assert "🤖 AI科技" not in text
    assert "1. 中文标题" in text
    assert "中文摘要。" in text
    assert "关注理由：与持仓相关" in text


def test_briefing_ignores_category_only_focus_directions() -> None:
    item = PersonalizedNewsItem(
        item=_item("A", "具体新闻摘要。", ["财经"]),
        display_category="财经",
    )

    text = build_briefing([item], focus_directions={"财经": ["财经"]})

    assert "- 财经：具体新闻摘要。" in text
    assert "- 财经：财经" not in text


def test_briefing_test_mode_prefix() -> None:
    items = [_item("A", "Hello world.", ["AI科技"])]
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
