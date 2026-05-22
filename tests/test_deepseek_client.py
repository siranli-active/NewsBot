from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from newsbot.deepseek_client import DeepSeekError, personalize_news
from newsbot.models import NewsItem


def _item(title: str, link: str) -> NewsItem:
    return NewsItem(
        title=title,
        link=link,
        summary="English summary",
        published_at=datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc),
        categories=["AI科技"],
        source="src",
    )


@patch("newsbot.deepseek_client.requests.post")
def test_personalize_news_maps_json_response(mock_post: Mock) -> None:
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "focus_directions": {"AI科技": ["AI资本开支"]},
                            "items": [
                                {
                                    "index": 1,
                                    "display_category": "AI科技",
                                    "translated_title": "中文标题",
                                    "translated_summary": "中文摘要",
                                    "importance_reason": "与持仓相关",
                                }
                            ],
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ]
    }
    mock_post.return_value = response

    briefing = personalize_news(
        api_key="secret-key",
        api_base="https://example.com",
        model="deepseek-chat",
        profile_summary="stock_positions: MSFT: 11.77%",
        candidates=[_item("A", "u0"), _item("B", "u1")],
        final_count=15,
        min_counts={"AI科技": 1},
    )

    assert briefing.focus_directions == {"AI科技": ["AI资本开支"]}
    assert briefing.items[0].item.title == "B"
    assert briefing.items[0].display_category == "AI科技"
    assert briefing.items[0].translated_title == "中文标题"
    call = mock_post.call_args
    assert call.kwargs["headers"]["Authorization"] == "Bearer secret-key"
    payload = call.kwargs["json"]
    assert payload["model"] == "deepseek-chat"
    assert payload["reasoning_effort"] == "high"
    assert payload["thinking"] == {"type": "enabled"}
    assert "temperature" not in payload
    prompt = payload["messages"][1]["content"]
    assert "stock_positions" in prompt
    assert "display_category" in prompt
    assert "最符合 profile 的一条具体新闻摘要" in prompt
    assert "不要写宽泛主题" in prompt
    assert "key_news" not in prompt
    assert "<system_instructions>" not in prompt
    assert "rate of return" not in prompt


@patch("newsbot.deepseek_client.requests.post")
def test_personalize_news_accepts_string_focus_direction(mock_post: Mock) -> None:
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "focus_directions": {"AI科技": "AI资本开支"},
                            "items": [{"index": 0}],
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ]
    }
    mock_post.return_value = response

    briefing = personalize_news(
        api_key="secret-key",
        api_base="https://example.com",
        model="deepseek-chat",
        profile_summary="stock_positions: MSFT: 11.77%",
        candidates=[_item("A", "u0")],
        final_count=15,
        min_counts={"AI科技": 1},
    )

    assert briefing.focus_directions == {"AI科技": ["AI资本开支"]}


@patch("newsbot.deepseek_client.requests.post")
def test_personalize_news_skips_untranslated_english_items(mock_post: Mock) -> None:
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "focus_directions": {},
                            "items": [{"index": 0}],
                        }
                    )
                }
            }
        ]
    }
    mock_post.return_value = response

    briefing = personalize_news(
        api_key="secret-key",
        api_base="https://example.com",
        model="deepseek-chat",
        profile_summary="stock_positions: MSFT: 11.77%",
        candidates=[_item("English title", "u0")],
        final_count=15,
        min_counts={"AI科技": 1},
    )

    assert briefing.items == []


@patch("newsbot.deepseek_client.requests.post")
def test_personalize_news_invalid_response_hides_sensitive_values(mock_post: Mock) -> None:
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"choices": [{"message": {"content": "not-json"}}]}
    mock_post.return_value = response

    with pytest.raises(DeepSeekError) as exc:
        personalize_news(
            api_key="secret-key",
            api_base="https://example.com",
            model="deepseek-chat",
            profile_summary="stock_positions: MSFT: 11.77%",
            candidates=[_item("A", "u0")],
            final_count=15,
            min_counts={"AI科技": 1},
        )

    message = str(exc.value)
    assert "secret-key" not in message
    assert "MSFT" not in message
