from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

INCLUDED_PROFILE_TAGS = {
    "tech_stack",
    "entity_type",
    "stock_investment",
    "stock_positions",
}
EXCLUDED_PROFILE_TAGS = {"basic_info", "environment", "stock_rate_of_return"}


def load_minimized_profile(path: str) -> str:
    root = ET.parse(Path(path)).getroot()
    parts: list[str] = []
    for element in root.iter():
        tag = element.tag.split("}")[-1]
        if tag in EXCLUDED_PROFILE_TAGS:
            continue
        if tag not in INCLUDED_PROFILE_TAGS:
            continue
        text = " ".join(" ".join(element.itertext()).split())
        if text:
            parts.append(f"{tag}: {_remove_return_lines(text)}")
    return "\n".join(parts)


def _remove_return_lines(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    kept = [line for line in lines if "return" not in line.lower() and "收益" not in line]
    if kept:
        return "\n".join(kept)
    return "" if "return" in text.lower() or "收益" in text else text
