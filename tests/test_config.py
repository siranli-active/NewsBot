from __future__ import annotations

import pytest

from newsbot.config import load_config


def test_load_config_sources_only(tmp_path, monkeypatch) -> None:
    path = tmp_path / "sources.yml"
    path.write_text(
        """
sources:
  - name: Example
    category: 财经
    url: https://example.com/rss.xml
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_BASE", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("PROFILE_XML_PATH", raising=False)

    cfg = load_config(str(path))

    assert cfg.sources[0].name == "Example"
    assert cfg.sources[0].category == "财经"
    assert cfg.arxiv_sources == []
    assert cfg.deepseek_api_key is None
    assert cfg.deepseek_api_base == "https://api.deepseek.com"
    assert cfg.deepseek_model == "deepseek-v4-flash"
    assert cfg.profile_xml_path == "profile.xml"


def test_load_config_deepseek_env(tmp_path, monkeypatch) -> None:
    path = tmp_path / "sources.yml"
    path.write_text(
        """
sources:
  - name: Example
    category: 财经
    url: https://example.com/rss.xml
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "key")
    monkeypatch.setenv("DEEPSEEK_API_BASE", "https://deepseek.example")
    monkeypatch.setenv("DEEPSEEK_MODEL", "model")
    monkeypatch.setenv("PROFILE_XML_PATH", "custom-profile.xml")

    cfg = load_config(str(path))

    assert cfg.deepseek_api_key == "key"
    assert cfg.deepseek_api_base == "https://deepseek.example"
    assert cfg.deepseek_model == "model"
    assert cfg.profile_xml_path == "custom-profile.xml"


def test_load_config_arxiv_sources(tmp_path) -> None:
    path = tmp_path / "sources.yml"
    path.write_text(
        """
sources:
  - name: Example
    category: 财经
    url: https://example.com/rss.xml
arxiv_sources:
  - name: arXiv Active Matter
    keywords:
      - active matter
    categories:
      - cond-mat.soft
""".strip(),
        encoding="utf-8",
    )

    cfg = load_config(str(path))

    source = cfg.arxiv_sources[0]
    assert source.name == "arXiv Active Matter"
    assert source.keywords == ["active matter"]
    assert source.categories == ["cond-mat.soft"]
    assert source.max_results == 5


def test_load_config_invalid_source_category(tmp_path) -> None:
    path = tmp_path / "sources.yml"
    path.write_text(
        """
sources:
  - name: Example
    category: 体育
    url: https://example.com/rss.xml
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="source.category"):
        load_config(str(path))


def test_load_config_missing_source_category(tmp_path) -> None:
    path = tmp_path / "sources.yml"
    path.write_text(
        """
sources:
  - name: Example
    url: https://example.com/rss.xml
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="category"):
        load_config(str(path))


def test_load_config_invalid_arxiv_sources(tmp_path) -> None:
    path = tmp_path / "sources.yml"
    path.write_text(
        """
sources:
  - name: Example
    category: 财经
    url: https://example.com/rss.xml
arxiv_sources:
  - name: arXiv Active Matter
    keywords: []
    categories:
      - cond-mat.soft
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="keywords"):
        load_config(str(path))
