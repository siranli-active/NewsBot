from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from newsbot.telegram_client import send_message


@patch("newsbot.telegram_client.requests.post")
def test_send_message_success(mock_post: Mock) -> None:
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {"ok": True}
    mock_post.return_value = resp

    send_message("token", "chat", "hello")

    mock_post.assert_called_once()


@patch("newsbot.telegram_client.requests.post")
def test_send_message_http_error(mock_post: Mock) -> None:
    resp = Mock()
    resp.status_code = 500
    resp.json.return_value = {"ok": False}
    mock_post.return_value = resp

    with pytest.raises(RuntimeError):
        send_message("token", "chat", "hello")


@patch("newsbot.telegram_client.requests.post")
def test_send_message_splits_long_text(mock_post: Mock) -> None:
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {"ok": True}
    mock_post.return_value = resp

    send_message("token", "chat", "x" * 4000)

    assert mock_post.call_count == 2
