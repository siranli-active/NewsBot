from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from newsbot.arxiv_client import fetch_all_arxiv, select_latest_arxiv
from newsbot.briefing import build_briefing
from newsbot.config import load_config, require_telegram_env
from newsbot.rss_client import fetch_all
from newsbot.selector import select_items
from newsbot.telegram_client import send_message


def should_include_arxiv(now: datetime | None = None) -> bool:
    london_now = now.astimezone(ZoneInfo("Europe/London")) if now else datetime.now(ZoneInfo("Europe/London"))
    return london_now.weekday() == 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="测试模式：最多发送3条，标题加【测试】")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不发送 Telegram")
    parser.add_argument("--max-items", type=int, default=18, help="最多发送多少条新闻")
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    if args.max_items <= 0:
        raise ValueError("--max-items 必须大于 0")

    cfg = load_config()
    items = fetch_all(cfg.sources)

    max_items = min(args.max_items, 3) if args.test else args.max_items
    selected = select_items(items, max_items=max_items)

    arxiv_selected = None
    if should_include_arxiv():
        arxiv_sources = getattr(cfg, "arxiv_sources", [])
        arxiv_items = fetch_all_arxiv(arxiv_sources) if arxiv_sources else []
        arxiv_selected = select_latest_arxiv(arxiv_items, max_items=5)

    message = build_briefing(selected, test_mode=args.test, arxiv_papers=arxiv_selected)

    if args.dry_run:
        print(message)
        return 0

    require_telegram_env(cfg)
    send_message(cfg.telegram_bot_token or "", cfg.telegram_chat_id or "", message)
    print("早报已发送")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
