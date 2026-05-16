from __future__ import annotations

import os
from dataclasses import dataclass

import yaml


NEWS_CATEGORIES = ["财经", "时政", "AI科技", "医疗卫生", "自然科学"]
COMBINED_CATEGORY_LIMIT = 4
COMBINED_LIMITED_CATEGORIES = {"医疗卫生", "自然科学"}


@dataclass
class Source:
    name: str
    url: str
    category: str


@dataclass
class ArxivSource:
    name: str
    keywords: list[str]
    categories: list[str]
    max_results: int = 5


@dataclass
class AppConfig:
    sources: list[Source]
    arxiv_sources: list[ArxivSource]
    telegram_bot_token: str | None
    telegram_chat_id: str | None


def _load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("sources.yml 必须是 YAML 对象")
    return data


def _parse_string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} 必须是非空列表")
    result = [str(item).strip() for item in value]
    if not all(result):
        raise ValueError(f"{field} 不能包含空值")
    return result


def _parse_sources(data: dict) -> list[Source]:
    items = data.get("sources", [])
    if not isinstance(items, list) or not items:
        raise ValueError("sources.yml 中必须包含非空 sources 列表")

    sources: list[Source] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("sources 列表项必须是对象")
        name = str(item.get("name", "")).strip()
        url = str(item.get("url", "")).strip()
        category = str(item.get("category", "")).strip()
        if not name or not url or not category:
            raise ValueError("每个 source 必须包含 name、url 和 category")
        if category not in NEWS_CATEGORIES:
            allowed = ", ".join(NEWS_CATEGORIES)
            raise ValueError(f"source.category 必须是以下之一：{allowed}")
        sources.append(Source(name=name, url=url, category=category))
    return sources


def _parse_arxiv_sources(data: dict) -> list[ArxivSource]:
    items = data.get("arxiv_sources", [])
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError("arxiv_sources 必须是列表")

    sources: list[ArxivSource] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("arxiv_sources 列表项必须是对象")
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError("每个 arxiv_source 必须包含 name")
        keywords = _parse_string_list(item.get("keywords"), "arxiv_source.keywords")
        categories = _parse_string_list(item.get("categories"), "arxiv_source.categories")
        max_results = int(item.get("max_results", 5))
        if max_results <= 0:
            raise ValueError("arxiv_source.max_results 必须大于 0")
        sources.append(
            ArxivSource(
                name=name,
                keywords=keywords,
                categories=categories,
                max_results=max_results,
            )
        )
    return sources


def load_sources(path: str = "sources.yml") -> list[Source]:
    return _parse_sources(_load_yaml(path))


def load_config(path: str = "sources.yml") -> AppConfig:
    data = _load_yaml(path)
    return AppConfig(
        sources=_parse_sources(data),
        arxiv_sources=_parse_arxiv_sources(data),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
    )


def require_telegram_env(cfg: AppConfig) -> None:
    if not cfg.telegram_bot_token:
        raise ValueError("缺少环境变量 TELEGRAM_BOT_TOKEN")
    if not cfg.telegram_chat_id:
        raise ValueError("缺少环境变量 TELEGRAM_CHAT_ID")
