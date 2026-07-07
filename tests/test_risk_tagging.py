from risklens.models import IntelligenceItem
from risklens.pipeline.tag_risks import tag_risks


def test_risk_tagging_detects_cybersecurity_terms():
    taxonomy = {"risk_tags": {"cybersecurity_risk": {"terms": ["cyber", "breach"]}}}
    item = IntelligenceItem(
        id="1", title="Cyber breach controls", url="https://example.com", source="AP"
    )
    tagged = tag_risks([item], taxonomy)[0]
    assert "cybersecurity_risk" in tagged.risk_tags
