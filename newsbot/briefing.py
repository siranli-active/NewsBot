from __future__ import annotations

from collections import Counter
from datetime import datetime

from newsbot.config import NEWS_CATEGORIES
from newsbot.models import NewsItem


FALLBACK_SUMMARY = "该新闻主要内容可参考原标题与原文链接。"
CATEGORY_EMOJIS = {
    "财经": "💰",
    "时政": "🏛️",
    "AI科技": "🤖",
    "医疗卫生": "🏥",
    "自然科学": "🔬",
}


def _truncate_to_two_sentences(text: str) -> str:
    raw = text.strip()
    if not raw:
        return FALLBACK_SUMMARY

    parts: list[str] = []
    buffer = ""
    for ch in raw:
        buffer += ch
        if ch in "。！？.!?":
            part = buffer.strip()
            if part:
                parts.append(part)
            buffer = ""
            if len(parts) == 2:
                break
    if len(parts) < 2 and buffer.strip():
        parts.append(buffer.strip())
    if not parts:
        return FALLBACK_SUMMARY
    return " ".join(parts[:2])


def _primary_category(item: NewsItem) -> str:
    for category in item.categories:
        if category in NEWS_CATEGORIES:
            return category
    return "综合"


def _top_category(items: list[NewsItem]) -> str:
    counter: Counter[str] = Counter()
    for item in items:
        category = _primary_category(item)
        if category != "综合":
            counter[category] += 1
    if not counter:
        return "综合"
    return counter.most_common(1)[0][0]


def _truncate_chars(text: str, limit: int = 300) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit]


def _format_authors(authors: list[str] | None) -> str:
    if not authors:
        return "未知"
    return ", ".join(authors[:2])


def _append_arxiv_section(lines: list[str], papers: list[NewsItem], test_mode: bool) -> None:
    lines.extend(["", "📚 每周 arXiv / Active Matter 论文", ""])
    if not papers:
        lines.append("过去一周内没有检索到 active matter 相关 arXiv 论文。")
        return

    for idx, paper in enumerate(papers, start=1):
        title = f"【测试】{paper.title}" if test_mode else paper.title
        lines.extend(
            [
                f"{idx}. {title}",
                f"   作者：{_format_authors(paper.authors)}",
                f"   摘要：{_truncate_chars(paper.summary)}",
                f"   {paper.link}",
                "",
            ]
        )


def build_briefing(
    items: list[NewsItem],
    test_mode: bool = False,
    arxiv_papers: list[NewsItem] | None = None,
) -> str:
    date_text = datetime.now().strftime("%Y-%m-%d")
    header = f"{'【测试】' if test_mode else ''}中文早间新闻简报（{date_text}）"

    top_category = _top_category(items)
    focus_titles = [f"- {i.title}" for i in items[:3]]
    if not focus_titles:
        focus_titles = ["- 暂无可用新闻"]

    lines: list[str] = [
        header,
        "",
        "今日重点",
        f"- 重点方向：{top_category}",
        "- 重点关注：",
        *focus_titles,
        "",
        "新闻列表",
    ]

    grouped: dict[str, list[NewsItem]] = {category: [] for category in NEWS_CATEGORIES}
    other_items: list[NewsItem] = []
    for item in items:
        category = _primary_category(item)
        if category in grouped:
            grouped[category].append(item)
        else:
            other_items.append(item)

    idx = 1
    for category in NEWS_CATEGORIES:
        category_items = grouped[category]
        if not category_items:
            continue
        lines.extend(["", f"{CATEGORY_EMOJIS[category]} {category}"])
        for item in category_items:
            title = f"【测试】{item.title}" if test_mode else item.title
            summary = _truncate_to_two_sentences(item.summary)
            lines.extend(
                [
                    f"{idx}. {title}",
                    f"   {summary}",
                    f"   {item.link}",
                    "",
                ]
            )
            idx += 1

    if other_items:
        lines.extend(["", "🗞️ 综合"])
        for item in other_items:
            title = f"【测试】{item.title}" if test_mode else item.title
            summary = _truncate_to_two_sentences(item.summary)
            lines.extend(
                [
                    f"{idx}. {title}",
                    f"   {summary}",
                    f"   {item.link}",
                    "",
                ]
            )
            idx += 1

    if idx == 1:
        lines.append("暂无可用新闻")

    if arxiv_papers is not None:
        _append_arxiv_section(lines, arxiv_papers, test_mode)

    return "\n".join(lines).strip()
