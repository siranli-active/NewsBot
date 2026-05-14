from __future__ import annotations

import requests


def send_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Telegram 发送失败，HTTP {resp.status_code}")
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError("Telegram 发送失败，接口返回 ok=false")
