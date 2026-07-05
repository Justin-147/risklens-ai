from __future__ import annotations

from pathlib import Path

import markdown


def write_html(path: Path, markdown_content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = markdown.markdown(markdown_content, extensions=["tables"])
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>RiskLens AI</title></head><body>{body}</body></html>"
    path.write_text(html, encoding="utf-8")
    return path
