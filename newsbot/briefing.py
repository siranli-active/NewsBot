from __future__ import annotations

from datetime import datetime

from newsbot.config import NEWS_CATEGORIES
from newsbot.models import NewsItem, PersonalizedNewsItem
from newsbot.selector import _category_for_selection


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


def _base_item(item: NewsItem | PersonalizedNewsItem) -> NewsItem:
    return item.item if isinstance(item, PersonalizedNewsItem) else item


def _primary_category(item: NewsItem | PersonalizedNewsItem) -> str:
    return _category_for_selection(item)


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


def _display_title(item: NewsItem | PersonalizedNewsItem, test_mode: bool) -> str:
    base = _base_item(item)
    title = item.translated_title if isinstance(item, PersonalizedNewsItem) and item.translated_title else base.title
    return f"【测试】{title}" if test_mode else title


def _display_summary(item: NewsItem | PersonalizedNewsItem) -> str:
    base = _base_item(item)
    summary = item.translated_summary if isinstance(item, PersonalizedNewsItem) and item.translated_summary else base.summary
    return _truncate_to_two_sentences(summary)


def _fallback_focus_directions(items: list[NewsItem | PersonalizedNewsItem]) -> list[str]:
    directions: list[str] = []
    seen: set[str] = set()
    for item in items:
        category = _primary_category(item)
        if category not in NEWS_CATEGORIES or category in seen:
            continue
        seen.add(category)
        directions.append(f"- {category}：{_display_summary(item)}")
    return directions or ["- 暂无可用新闻"]


def build_briefing(
    items: list[NewsItem | PersonalizedNewsItem],
    test_mode: bool = False,
    arxiv_papers: list[NewsItem] | None = None,
    focus_directions: dict[str, list[str]] | None = None,
) -> str:
    date_text = datetime.now().strftime("%Y-%m-%d")
    header = f"{'【测试】' if test_mode else ''}中文早间新闻简报（{date_text}）"

    directions = []
    for category in NEWS_CATEGORIES:
        for direction in (focus_directions or {}).get(category, []):
            text = direction.strip()
            if text and text != category:
                directions.append(f"- {category}：{text}")
    if not directions:
        directions = _fallback_focus_directions(items)

    lines: list[str] = [
        header,
        "",
        "今日重点",
        "重点方向：",
        *directions,
        "",
        "新闻列表",
    ]

    grouped: dict[str, list[NewsItem | PersonalizedNewsItem]] = {category: [] for category in NEWS_CATEGORIES}
    other_items: list[NewsItem | PersonalizedNewsItem] = []
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
            base = _base_item(item)
            lines.extend([f"{idx}. {_display_title(item, test_mode)}", f"   {_display_summary(item)}"])
            if isinstance(item, PersonalizedNewsItem) and item.importance_reason:
                lines.append(f"   关注理由：{item.importance_reason}")
            lines.extend([f"   {base.link}", ""])
            idx += 1

    if other_items:
        lines.extend(["", "🗞️ 综合"])
        for item in other_items:
            base = _base_item(item)
            lines.extend([f"{idx}. {_display_title(item, test_mode)}", f"   {_display_summary(item)}"])
            if isinstance(item, PersonalizedNewsItem) and item.importance_reason:
                lines.append(f"   关注理由：{item.importance_reason}")
            lines.extend([f"   {base.link}", ""])
            idx += 1

    if idx == 1:
        lines.append("暂无可用新闻")

    if arxiv_papers is not None:
        _append_arxiv_section(lines, arxiv_papers, test_mode)

    return "\n".join(lines).strip()
