from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

from newsbot.arxiv_client import fetch_all_arxiv, select_latest_arxiv
from newsbot.briefing import build_briefing
from newsbot.config import (
    DEFAULT_CANDIDATE_ITEMS,
    DEFAULT_FINAL_ITEMS,
    MIN_FINAL_CATEGORY_COUNTS,
    REQUIRED_FINAL_CATEGORY_COUNTS,
    load_config,
    require_telegram_env,
)
from newsbot.deepseek_client import DeepSeekError, personalize_news
from newsbot.models import PersonalizedBriefing, PersonalizedNewsItem
from newsbot.profile import load_minimized_profile
from newsbot.rss_client import fetch_all
from newsbot.selector import enforce_category_requirements, select_candidates, select_items
from newsbot.telegram_client import send_message


def should_include_arxiv(now: datetime | None = None) -> bool:
    london_now = now.astimezone(ZoneInfo("Europe/London")) if now else datetime.now(ZoneInfo("Europe/London"))
    return london_now.weekday() == 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="测试模式：最多发送3条，标题加【测试】")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不发送 Telegram")
    parser.add_argument("--max-items", type=int, default=DEFAULT_FINAL_ITEMS, help="最多发送多少条新闻")
    parser.add_argument("--candidate-items", type=int, default=DEFAULT_CANDIDATE_ITEMS, help="DeepSeek 筛选前最多收集多少条候选新闻")
    return parser.parse_args()


def _build_personalized_briefing(cfg: object, candidates: list, max_items: int) -> PersonalizedBriefing | None:
    api_key = getattr(cfg, "deepseek_api_key", None)
    if not api_key:
        print("DeepSeek personalization skipped: DEEPSEEK_API_KEY is not set")
        return None
    try:
        profile_path = getattr(cfg, "profile_xml_path", "profile.xml")
        profile_summary = load_minimized_profile(profile_path)
        briefing = personalize_news(
            api_key=api_key,
            api_base=getattr(cfg, "deepseek_api_base"),
            model=getattr(cfg, "deepseek_model"),
            profile_summary=profile_summary,
            candidates=candidates,
            final_count=max_items,
            min_counts=MIN_FINAL_CATEGORY_COUNTS,
        )
    except OSError as exc:
        print(f"DeepSeek personalization skipped: could not read profile file ({exc.__class__.__name__})")
        return None
    except ET.ParseError:
        print("DeepSeek personalization skipped: profile XML is invalid")
        return None
    except DeepSeekError as exc:
        print(f"DeepSeek personalization skipped: {exc}")
        return None

    print(f"DeepSeek personalization used: {len(briefing.items)} items returned")
    selected = enforce_category_requirements(
        briefing.items,
        [item.item for item in briefing.items],
        max_items=max_items,
        exact_counts=REQUIRED_FINAL_CATEGORY_COUNTS,
        min_counts=MIN_FINAL_CATEGORY_COUNTS,
    )
    return PersonalizedBriefing(
        items=[item for item in selected if isinstance(item, PersonalizedNewsItem)],
        focus_directions=briefing.focus_directions,
    )


def run() -> int:
    args = parse_args()
    if args.max_items <= 0:
        raise ValueError("--max-items 必须大于 0")
    if args.candidate_items <= 0:
        raise ValueError("--candidate-items 必须大于 0")

    cfg = load_config()
    items = fetch_all(cfg.sources)

    max_items = min(args.max_items, 3) if args.test else args.max_items
    candidates = select_candidates(items, max_items=args.candidate_items)
    personalized = None if args.test else _build_personalized_briefing(cfg, candidates, max_items)
    selected = personalized.items if personalized else [PersonalizedNewsItem(item=item) for item in select_items(candidates, max_items=max_items)]

    arxiv_selected = None
    if should_include_arxiv():
        arxiv_sources = getattr(cfg, "arxiv_sources", [])
        arxiv_items = fetch_all_arxiv(arxiv_sources) if arxiv_sources else []
        arxiv_selected = select_latest_arxiv(arxiv_items, max_items=5)

    message = build_briefing(
        selected,
        test_mode=args.test,
        arxiv_papers=arxiv_selected,
        focus_directions=personalized.focus_directions if personalized else None,
    )

    if args.dry_run:
        print(message)
        return 0

    require_telegram_env(cfg)
    send_message(cfg.telegram_bot_token or "", cfg.telegram_chat_id or "", message)
    print("早报已发送")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
