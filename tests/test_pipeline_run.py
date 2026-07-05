from pathlib import Path

from risklens.main import run_report


def test_run_report_mock_generates_outputs():
    outputs = run_report("ai_technology_strategy", mock=True)
    for path in outputs.values():
        assert Path(path).exists()
    assert "RiskLens AI Brief" in Path(outputs["markdown_en"]).read_text(encoding="utf-8")
    assert "RiskLens AI 简报" in Path(outputs["markdown_zh"]).read_text(encoding="utf-8")