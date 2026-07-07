from pathlib import Path

from risklens.main import parse_as_of, run_report


def test_run_report_mock_generates_outputs():
    outputs = run_report("ai_technology_strategy", mock=True)
    for path in outputs.values():
        assert Path(path).exists()
    assert "RiskLens AI Brief" in Path(outputs["markdown_en"]).read_text(encoding="utf-8")
    assert "RiskLens AI 简报" in Path(outputs["markdown_zh"]).read_text(encoding="utf-8")


def test_run_report_supports_as_of_and_output_root(tmp_path):
    as_of = parse_as_of("2026-07-06")
    outputs = run_report(
        "financial_services",
        mock=True,
        generated_at=as_of,
        output_root=tmp_path,
    )

    assert Path(outputs["processed"]).is_relative_to(tmp_path)
    assert Path(outputs["processed"]).name == "2026-07-06_financial_services.json"
    assert "2026-07-06" in Path(outputs["markdown_en"]).read_text(encoding="utf-8")
