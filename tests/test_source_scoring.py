from risklens.models import IntelligenceItem, SourceType
from risklens.pipeline.score_sources import score_sources


def test_regulatory_sources_receive_high_authority_score():
    item = IntelligenceItem(
        id="1",
        title="Policy",
        url="https://example.com",
        source="SEC",
        source_type=SourceType.regulatory,
    )
    scored = score_sources([item])[0]
    assert scored.authority_score >= 0.9
