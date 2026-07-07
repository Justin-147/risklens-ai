from pathlib import Path


def test_dashboard_source_does_not_contain_mojibake_chinese_label():
    text = Path("src/risklens/dashboard/app.py").read_text(encoding="utf-8")
    assert '"中文"' in text
    assert "涓" not in text
    assert "use_container_width=True" in text
