from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

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
