from __future__ import annotations

import json
from typing import Any

import requests

from newsbot.config import NEWS_CATEGORIES
from newsbot.models import NewsItem, PersonalizedBriefing, PersonalizedNewsItem


class DeepSeekError(RuntimeError):
    pass


def personalize_news(
    api_key: str,
    api_base: str,
    model: str,
    profile_summary: str,
    candidates: list[NewsItem],
    final_count: int,
    min_counts: dict[str, int],
) -> PersonalizedBriefing:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是中文新闻筛选助手。只返回合法 JSON，不要 markdown，不要解释。",
            },
            {
                "role": "user",
                "content": _build_prompt(profile_summary, candidates, final_count, min_counts),
            },
        ],
        "reasoning_effort": "high",
        "thinking": {"type": "enabled"},
        "response_format": {"type": "json_object"},
    }
    try:
        response = requests.post(
            f"{api_base.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        raise DeepSeekError("DeepSeek 请求失败") from exc

    if response.status_code >= 400:
        raise DeepSeekError(f"DeepSeek 返回 HTTP {response.status_code}")

    try:
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise DeepSeekError("DeepSeek 返回格式无效") from exc

    return _parse_personalized_briefing(data, candidates, final_count)


def _build_prompt(profile_summary: str, candidates: list[NewsItem], final_count: int, min_counts: dict[str, int]) -> str:
    news = []
    for index, item in enumerate(candidates):
        news.append(
            {
                "index": index,
                "title": item.title,
                "summary": item.summary,
                "source": item.source,
                "link": item.link,
                "categories": item.categories,
                "published_at": item.published_at.isoformat() if item.published_at else None,
            }
        )
    return json.dumps(
        {
            "task": "根据用户最小化画像，从候选新闻中筛选最重要的新闻并生成中文简报素材。",
            "privacy_note": "profile 已在本地最小化；不要推断或输出未提供的个人信息。",
            "profile": profile_summary,
            "requirements": {
                "final_count": final_count,
                "categories": "最终新闻需覆盖财经、时政、AI科技、医疗卫生、自然科学；候选不足时尽量满足。",
                "minimum_counts": min_counts,
                "focus_directions": "返回按分类组织的对象，key 必须是财经、时政、AI科技、医疗卫生、自然科学。每个 value 必须是该分类最终入选 items 中最符合 profile 的一条具体新闻摘要，说明这条新闻本身发生了什么以及为什么值得该用户关注；不要写宽泛主题、关注方向清单或分类说明。若某分类没有最终入选新闻，不要为该分类生成 value。",
                "display_category": "每条 item 必须给出 display_category，且只能是财经、时政、AI科技、医疗卫生、自然科学之一。医疗、公共卫生、生物医药归医疗卫生；航天、物理、基础科学、天文归自然科学；只有 AI、软件、半导体、平台、科技产业主线才归 AI科技。",
                "translation": "英文新闻必须提供中文标题和中文摘要；中文新闻可提供压缩后的中文要点。",
                "output": "只返回 JSON，包含 focus_directions、items。items 每项包含 index、display_category、translated_title、translated_summary、importance_reason。",
            },
            "candidates": news,
        },
        ensure_ascii=False,
    )


def _parse_personalized_briefing(data: dict[str, Any], candidates: list[NewsItem], final_count: int) -> PersonalizedBriefing:
    raw_items = data.get("items")
    if not isinstance(raw_items, list):
        raise DeepSeekError("DeepSeek 返回缺少 items")

    items: list[PersonalizedNewsItem] = []
    seen: set[int] = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        index = raw.get("index")
        if not isinstance(index, int) or index in seen or index < 0 or index >= len(candidates):
            continue
        item = candidates[index]
        translated_title = _optional_string(raw.get("translated_title"))
        translated_summary = _optional_string(raw.get("translated_summary"))
        if not translated_title and not _contains_cjk(item.title):
            continue
        if item.summary and not translated_summary and not _contains_cjk(item.summary):
            continue
        seen.add(index)
        items.append(
            PersonalizedNewsItem(
                item=item,
                translated_title=translated_title,
                translated_summary=translated_summary,
                importance_reason=_optional_string(raw.get("importance_reason")),
                display_category=_optional_category(raw.get("display_category")),
            )
        )
        if len(items) == final_count:
            break

    return PersonalizedBriefing(
        items=items,
        focus_directions=_category_direction_map(data.get("focus_directions")),
    )


def _optional_string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _optional_category(value: object) -> str | None:
    text = _optional_string(value)
    return text if text in NEWS_CATEGORIES else None


def _string_list(value: object) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _category_direction_map(value: object) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    directions: dict[str, list[str]] = {}
    for category in NEWS_CATEGORIES:
        category_directions = _string_list(value.get(category))
        if category_directions:
            directions[category] = category_directions
    return directions
