from datetime import UTC, datetime

from risklens.llm.mock_provider import MockLLMProvider
from risklens.models import IntelligenceItem, SourceType
from risklens.pipeline.build_context import build_report_context
from risklens.writers.html_writer import write_html


def test_report_escapes_markdown_table_and_html_body(tmp_path):
    item = IntelligenceItem(
        id="unsafe",
        title="Bad | <script>alert(1)</script>",
        url="javascript:alert(1)",
        source="Source | <script>",
        source_type=SourceType.media,
        published_at=datetime(2026, 7, 6, tzinfo=UTC),
        summary="Summary | <script>alert(1)</script>",
        raw_text="Summary | <script>alert(1)</script>",
        risk_tags=["model_risk"],
    )
    context = build_report_context("Unsafe Demo", [item], generated_at=datetime(2026, 7, 6))
    markdown = MockLLMProvider().generate_report(context)
    html_path = write_html(tmp_path / "report.html", markdown, title="Bad <script>")
    html = html_path.read_text(encoding="utf-8")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html or "&amp;lt;script&amp;gt;" in html
    assert r"\|" in markdown
    assert "javascript:alert" not in markdown
