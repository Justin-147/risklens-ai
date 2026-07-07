from __future__ import annotations

import re
from html import escape


def safe_text(value: object) -> str:
    if value is None:
        return ""
    text = escape(str(value), quote=True)
    text = text.replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def md_cell(value: object) -> str:
    text = safe_text(value)
    return text.replace("|", r"\|")


def safe_url(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if not text.startswith(("http://", "https://")):
        return "#"
    if any(token in text for token in ["\r", "\n", "|", " "]):
        return "#"
    return text
