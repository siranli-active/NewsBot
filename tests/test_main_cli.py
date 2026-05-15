from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from newsbot.config import ArxivSource
from newsbot.models import NewsItem


def _items(n: int) -> list[NewsItem]:
    return [
        NewsItem(
            title=f"t{i}",
            link=f"u{i}",
            summary="s",
            published_at=datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc),
            categories=["Tech"],
            source="src",
        )
        for i in range(n)
    ]


@patch("main.send_message")
@patch("main.fetch_all")
@patch("main.load_config")
def test_dry_run_not_send(mock_cfg, mock_fetch, mock_send, monkeypatch, capsys):
    import main

    class Cfg:
        sources = []
        telegram_bot_token = "token"
        telegram_chat_id = "chat"

    mock_cfg.return_value = Cfg()
    mock_fetch.return_value = _items(5)
    monkeypatch.setattr("sys.argv", ["main.py", "--dry-run"])

    rc = main.run()
    out = capsys.readouterr().out

    assert rc == 0
    assert "中文早间新闻简报" in out
    mock_send.assert_not_called()


@patch("main.send_message")
@patch("main.fetch_all")
@patch("main.load_config")
def test_test_mode_cap_3_items(mock_cfg, mock_fetch, mock_send, monkeypatch):
    import main

    class Cfg:
        sources = []
        telegram_bot_token = "token"
        telegram_chat_id = "chat"

    mock_cfg.return_value = Cfg()
    mock_fetch.return_value = _items(10)
    monkeypatch.setattr("sys.argv", ["main.py", "--test"])

    rc = main.run()

    assert rc == 0
    sent_text = mock_send.call_args.args[2]
    assert "4." not in sent_text
    assert "【测试】" in sent_text


@patch("main.send_message")
@patch("main.fetch_all_arxiv")
@patch("main.fetch_all")
@patch("main.load_config")
def test_arxiv_sources_included(mock_cfg, mock_fetch, mock_fetch_arxiv, mock_send, monkeypatch):
    import main

    class Cfg:
        sources = []
        arxiv_sources = [
            ArxivSource(
                name="arXiv Active Matter",
                keywords=["active matter"],
                categories=["cond-mat.soft"],
            )
        ]
        telegram_bot_token = "token"
        telegram_chat_id = "chat"

    mock_cfg.return_value = Cfg()
    mock_fetch.return_value = []
    mock_fetch_arxiv.return_value = [
        NewsItem(
            title="Active matter paper",
            link="https://arxiv.org/abs/2605.00001",
            summary="Abstract",
            published_at=datetime(2026, 5, 15, 8, 0, tzinfo=timezone.utc),
            categories=["cond-mat.soft"],
            source="arXiv Active Matter",
            authors=["Author One", "Author Two"],
        )
    ]
    monkeypatch.setattr("sys.argv", ["main.py"])

    rc = main.run()

    assert rc == 0
    mock_fetch_arxiv.assert_called_once_with(Cfg.arxiv_sources)
    sent_text = mock_send.call_args.args[2]
    assert "📚 每周 arXiv / Active Matter 论文" in sent_text
    assert "Active matter paper" in sent_text
