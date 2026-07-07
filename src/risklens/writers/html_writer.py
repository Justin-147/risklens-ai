from __future__ import annotations

from html import escape
from pathlib import Path

import markdown


def write_html(path: Path, markdown_content: str, title: str = "RiskLens AI") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_title = escape(title, quote=True)
    safe_markdown = escape(markdown_content, quote=False)
    body = markdown.markdown(safe_markdown, extensions=["tables"])
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
</head>
<body>
  <main>
    <div class="disclaimer">
      Prototype only. Not investment advice. Not trading advice.
      Not legal, compliance, or financial advice.
    </div>
    {body}
  </main>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
    return path
