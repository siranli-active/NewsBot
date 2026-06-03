from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from unittest.mock import patch

from newsbot.arxiv_client import ArxivFetchError
from newsbot.config import ArxivSource
from newsbot.models import NewsItem, PersonalizedBriefing, PersonalizedNewsItem


def _items(n: int, category: str = "AI科技") -> list[NewsItem]:
    return [
        NewsItem(
            title=f"t{i}",
            link=f"u{i}",
            summary="s",
            published_at=datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc),
            categories=[category],
            source="src",
        )
        for i in range(n)
    ]


def _mixed_items() -> list[NewsItem]:
    items: list[NewsItem] = []
    for category in ["财经", "时政", "AI科技", "医疗卫生", "自然科学"]:
        items.extend(_items(6, category=category))
    return [
        NewsItem(
            title=f"{item.categories[0]}-{index}",
            link=f"u{index}",
            summary=item.summary,
            published_at=item.published_at,
            categories=item.categories,
            source=item.source,
        )
        for index, item in enumerate(items)
    ]


class Cfg:
    sources = []
    arxiv_sources: list[ArxivSource] = []
    telegram_bot_token = "token"
    telegram_chat_id = "chat"
    deepseek_api_key = None
    deepseek_api_base = "https://api.deepseek.com"
    deepseek_model = "deepseek-chat"
    profile_xml_path = "profile.xml"


@patch("main.send_message")
@patch("main.fetch_all")
@patch("main.load_config")
def test_dry_run_not_send(mock_cfg, mock_fetch, mock_send, monkeypatch, capsys):
    import main

    mock_cfg.return_value = Cfg()
    mock_fetch.return_value = _mixed_items()
    monkeypatch.setattr("sys.argv", ["main.py", "--dry-run"])
    monkeypatch.setattr(main, "should_include_arxiv", lambda: False)

    rc = main.run()
    out = capsys.readouterr().out

    assert rc == 0
    assert "中文早间新闻简报" in out
    mock_send.assert_not_called()


@patch("main.send_message")
@patch("main.fetch_all")
@patch("main.load_config")
def test_default_cap_15_items(mock_cfg, mock_fetch, mock_send, monkeypatch):
    import main

    mock_cfg.return_value = Cfg()
    mock_fetch.return_value = _mixed_items()
    monkeypatch.setattr("sys.argv", ["main.py"])
    monkeypatch.setattr(main, "should_include_arxiv", lambda: False)

    rc = main.run()

    assert rc == 0
    sent_text = mock_send.call_args.args[2]
    assert "16." in sent_text
    assert "17." not in sent_text


@patch("main.send_message")
@patch("main.personalize_news")
@patch("main.load_minimized_profile")
@patch("main.fetch_all")
@patch("main.load_config")
def test_deepseek_called_with_30_candidates(mock_cfg, mock_fetch, mock_profile, mock_personalize, mock_send, monkeypatch):
    import main

    cfg = Cfg()
    cfg.deepseek_api_key = "key"
    mock_cfg.return_value = cfg
    mock_fetch.return_value = _items(40)
    mock_profile.return_value = "stock_positions: MSFT: 11.77%"
    mock_personalize.return_value = PersonalizedBriefing(
        items=[PersonalizedNewsItem(item=item) for item in _items(16)],
        focus_directions={"AI科技": ["方向"]},
    )
    monkeypatch.setattr("sys.argv", ["main.py"])
    monkeypatch.setattr(main, "should_include_arxiv", lambda: False)

    rc = main.run()

    assert rc == 0
    assert len(mock_personalize.call_args.kwargs["candidates"]) == 30
    sent_text = mock_send.call_args.args[2]
    assert "- AI科技：方向" in sent_text
    assert "重点关注：" not in sent_text


@patch("main.send_message")
@patch("main.personalize_news")
@patch("main.load_minimized_profile")
@patch("main.fetch_all")
@patch("main.load_config")
def test_deepseek_output_fills_missing_categories_from_renderable_candidates(
    mock_cfg, mock_fetch, mock_profile, mock_personalize, mock_send, monkeypatch
):
    import main

    cfg = Cfg()
    cfg.deepseek_api_key = "key"
    mock_cfg.return_value = cfg
    items = [
        NewsItem(
            title=item.title,
            link=item.link,
            summary="中文摘要。",
            published_at=item.published_at,
            categories=item.categories,
            source=item.source,
        )
        for item in _mixed_items()
    ]
    mock_fetch.return_value = items
    mock_profile.return_value = "stock_positions: MSFT: 11.77%"
    mock_personalize.return_value = PersonalizedBriefing(
        items=[PersonalizedNewsItem(item=item, translated_title=f"中文{index}", translated_summary="中文摘要。") for index, item in enumerate(items[12:16])],
        focus_directions={"AI科技": ["中文重点"]},
    )
    monkeypatch.setattr("sys.argv", ["main.py"])
    monkeypatch.setattr(main, "should_include_arxiv", lambda: False)

    rc = main.run()

    assert rc == 0
    sent_text = mock_send.call_args.args[2]
    assert "💰 财经" in sent_text
    assert "🏛️ 时政" in sent_text
    assert "16." in sent_text


@patch("main.send_message")
@patch("main.personalize_news")
@patch("main.load_minimized_profile")
@patch("main.fetch_all")
@patch("main.load_config")
def test_deepseek_output_does_not_add_untranslated_candidates(
    mock_cfg, mock_fetch, mock_profile, mock_personalize, mock_send, monkeypatch
):
    import main

    cfg = Cfg()
    cfg.deepseek_api_key = "key"
    mock_cfg.return_value = cfg
    items = _items(10)
    mock_fetch.return_value = items
    mock_profile.return_value = "stock_positions: MSFT: 11.77%"
    mock_personalize.return_value = PersonalizedBriefing(
        items=[
            PersonalizedNewsItem(
                item=items[0],
                translated_title="中文标题",
                translated_summary="中文摘要。",
                display_category="AI科技",
            )
        ],
        focus_directions={"AI科技": ["中文重点"]},
    )
    monkeypatch.setattr("sys.argv", ["main.py"])
    monkeypatch.setattr(main, "should_include_arxiv", lambda: False)

    rc = main.run()

    assert rc == 0
    sent_text = mock_send.call_args.args[2]
    assert "1. 中文标题" in sent_text
    assert "2. t" not in sent_text


@patch("main.send_message")
@patch("main.personalize_news")
@patch("main.fetch_all")
@patch("main.load_config")
def test_test_mode_skips_deepseek(mock_cfg, mock_fetch, mock_personalize, mock_send, monkeypatch):
    import main

    cfg = Cfg()
    cfg.deepseek_api_key = "key"
    mock_cfg.return_value = cfg
    mock_fetch.return_value = _items(10)
    monkeypatch.setattr("sys.argv", ["main.py", "--test"])
    monkeypatch.setattr(main, "should_include_arxiv", lambda: False)

    rc = main.run()

    assert rc == 0
    mock_personalize.assert_not_called()
    sent_text = mock_send.call_args.args[2]
    assert "4." not in sent_text
    assert "【测试】" in sent_text


@patch("main.send_message")
@patch("main.fetch_all_arxiv")
@patch("main.fetch_all")
@patch("main.load_config")
def test_arxiv_sources_included(mock_cfg, mock_fetch, mock_fetch_arxiv, mock_send, monkeypatch):
    import main

    class ArxivCfg(Cfg):
        arxiv_sources = [
            ArxivSource(
                name="arXiv Active Matter",
                keywords=["active matter"],
                categories=["cond-mat.soft"],
            )
        ]

    mock_cfg.return_value = ArxivCfg()
    mock_fetch.return_value = []
    mock_fetch_arxiv.return_value = [
        NewsItem(
            title="Active matter paper",
            link="https://arxiv.org/abs/2605.00001",
            summary="Abstract",
            published_at=datetime.now(timezone.utc) - timedelta(days=1),
            categories=["cond-mat.soft"],
            source="arXiv Active Matter",
            authors=["Author One", "Author Two"],
        )
    ]
    monkeypatch.setattr("sys.argv", ["main.py"])
    monkeypatch.setattr(main, "should_include_arxiv", lambda: True)

    rc = main.run()

    assert rc == 0
    mock_fetch_arxiv.assert_called_once_with(ArxivCfg.arxiv_sources)
    sent_text = mock_send.call_args.args[2]
    assert "📚 每周 arXiv / Active Matter 论文" in sent_text
    assert "Active matter paper" in sent_text


@patch("main.send_message")
@patch("main.fetch_all_arxiv")
@patch("main.fetch_all")
@patch("main.load_config")
def test_arxiv_fetch_error_is_included_in_briefing(mock_cfg, mock_fetch, mock_fetch_arxiv, mock_send, monkeypatch):
    import main

    class ArxivCfg(Cfg):
        arxiv_sources = [
            ArxivSource(
                name="arXiv Active Matter",
                keywords=["active matter"],
                categories=["cond-mat.soft"],
            )
        ]

    mock_cfg.return_value = ArxivCfg()
    mock_fetch.return_value = []
    mock_fetch_arxiv.side_effect = ArxivFetchError("arXiv API returned HTTP 429")
    monkeypatch.setattr("sys.argv", ["main.py"])
    monkeypatch.setattr(main, "should_include_arxiv", lambda: True)

    rc = main.run()

    assert rc == 0
    sent_text = mock_send.call_args.args[2]
    assert "📚 每周 arXiv / Active Matter 论文" in sent_text
    assert "arXiv active matter 论文检索失败：arXiv API returned HTTP 429" in sent_text


@patch("main.send_message")
@patch("main.fetch_all_arxiv")
@patch("main.fetch_all")
@patch("main.load_config")
def test_arxiv_sources_skipped_on_non_wednesday(mock_cfg, mock_fetch, mock_fetch_arxiv, mock_send, monkeypatch):
    import main

    class ArxivCfg(Cfg):
        arxiv_sources = [
            ArxivSource(
                name="arXiv Active Matter",
                keywords=["active matter"],
                categories=["cond-mat.soft"],
            )
        ]

    mock_cfg.return_value = ArxivCfg()
    mock_fetch.return_value = []
    monkeypatch.setattr("sys.argv", ["main.py"])
    monkeypatch.setattr(main, "should_include_arxiv", lambda: False)

    rc = main.run()

    assert rc == 0
    mock_fetch_arxiv.assert_not_called()
    sent_text = mock_send.call_args.args[2]
    assert "📚 每周 arXiv / Active Matter 论文" not in sent_text


def test_should_include_arxiv_only_on_london_wednesday():
    import main

    wednesday = datetime(2026, 5, 20, 8, 0, tzinfo=ZoneInfo("Europe/London"))
    thursday = datetime(2026, 5, 21, 8, 0, tzinfo=ZoneInfo("Europe/London"))

    assert main.should_include_arxiv(wednesday) is True
    assert main.should_include_arxiv(thursday) is False
