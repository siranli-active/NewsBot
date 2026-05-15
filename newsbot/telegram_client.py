from __future__ import annotations

import requests


MAX_MESSAGE_LENGTH = 3900


def _split_message(text: str) -> list[str]:
    chunks: list[str] = []
    current = ""

    for line in text.splitlines(keepends=True):
        if len(line) > MAX_MESSAGE_LENGTH:
            if current:
                chunks.append(current.rstrip())
                current = ""
            chunks.extend(line[i : i + MAX_MESSAGE_LENGTH].rstrip() for i in range(0, len(line), MAX_MESSAGE_LENGTH))
        elif len(current) + len(line) > MAX_MESSAGE_LENGTH:
            chunks.append(current.rstrip())
            current = line
        else:
            current += line

    if current:
        chunks.append(current.rstrip())
    return chunks or [""]


def send_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for chunk in _split_message(text):
        resp = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        try:
            data = resp.json()
        except ValueError:
            data = {}
        description = data.get("description") if isinstance(data, dict) else None
        detail = f": {description}" if description else ""

        if resp.status_code != 200:
            raise RuntimeError(f"Telegram 发送失败，HTTP {resp.status_code}{detail}")
        if not data.get("ok"):
            raise RuntimeError(f"Telegram 发送失败，接口返回 ok=false{detail}")
