from datetime import UTC, datetime

from risklens.main import run_report
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType


def test_non_mock_mode_uses_fetchers(monkeypatch):
    called = {"fetchers": False}

    def fake_collect(profile: str):
        called["fetchers"] = True
        return [
            IntelligenceItem(
                id="fetcher-item",
                title="Regulatory policy signal for banking AI",
                url="https://example.com/fetcher-item",
                source="Test Regulator",
                source_type=SourceType.regulatory,
                published_at=datetime.now(UTC),
                summary="Regulatory policy signal for banking AI model risk.",
                raw_text="Regulatory policy signal for banking AI model risk.",
                evidence_level=EvidenceLevel.primary,
            )
        ]

    def fail_mock(profile: str):
        raise AssertionError("mock_items should not be called in non-mock mode")

    monkeypatch.setattr("risklens.main.collect_items_from_fetchers", fake_collect)
    monkeypatch.setattr("risklens.main.mock_items", fail_mock)
    outputs = run_report("financial_services", mock=False)
    assert called["fetchers"]
    assert outputs["markdown_en"].exists()
