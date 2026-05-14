from __future__ import annotations

from collections import Counter
from datetime import datetime

from newsbot.models import NewsItem


FALLBACK_SUMMARY = "该新闻主要内容可参考原标题与原文链接。"


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


def _top_category(items: list[NewsItem]) -> str:
    counter: Counter[str] = Counter()
    for item in items:
        for cat in item.categories:
            if cat.strip():
                counter[cat.strip()] += 1
    if not counter:
        return "综合"
    return counter.most_common(1)[0][0]


def build_briefing(items: list[NewsItem], test_mode: bool = False) -> str:
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

    for idx, item in enumerate(items, start=1):
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

    return "\n".join(lines).strip()
