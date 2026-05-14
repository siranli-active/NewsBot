from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from newsbot.config import Source
from newsbot.rss_client import fetch_source


@patch("newsbot.rss_client.feedparser.parse")
def test_fetch_source_extracts_fields(mock_parse):
    class Feed:
        entries = [
            {
                "title": "t1",
                "link": "u1",
                "summary": "s1",
                "published": "2026-05-14T06:00:00Z",
                "tags": [{"term": "Tech"}],
            },
            {
                "title": "t2",
                "link": "u2",
                "description": "d2",
            },
        ]

    mock_parse.return_value = Feed()

    out = fetch_source(Source(name="n", url="https://x"))
    assert len(out) == 2
    assert out[0].summary == "s1"
    assert out[0].published_at == datetime(2026, 5, 14, 6, 0, tzinfo=timezone.utc)
    assert out[0].categories == ["Tech"]
    assert out[1].summary == "d2"
    assert out[1].published_at is None
