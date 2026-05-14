from __future__ import annotations

import os
from dataclasses import dataclass

import yaml


@dataclass
class Source:
    name: str
    url: str


@dataclass
class AppConfig:
    sources: list[Source]
    telegram_bot_token: str | None
    telegram_chat_id: str | None


def load_sources(path: str = "sources.yml") -> list[Source]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    items = data.get("sources", [])
    if not isinstance(items, list) or not items:
        raise ValueError("sources.yml 中必须包含非空 sources 列表")

    sources: list[Source] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("sources 列表项必须是对象")
        name = str(item.get("name", "")).strip()
        url = str(item.get("url", "")).strip()
        if not name or not url:
            raise ValueError("每个 source 必须包含 name 和 url")
        sources.append(Source(name=name, url=url))
    return sources


def load_config(path: str = "sources.yml") -> AppConfig:
    return AppConfig(
        sources=load_sources(path),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
    )


def require_telegram_env(cfg: AppConfig) -> None:
    if not cfg.telegram_bot_token:
        raise ValueError("缺少环境变量 TELEGRAM_BOT_TOKEN")
    if not cfg.telegram_chat_id:
        raise ValueError("缺少环境变量 TELEGRAM_CHAT_ID")
