from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class SourceType(str, Enum):
    official = "official"
    regulatory = "regulatory"
    academic = "academic"
    media = "media"
    market = "market"
    company = "company"
    other = "other"


class EvidenceLevel(str, Enum):
    primary = "primary"
    secondary = "secondary"
    unverified = "unverified"


class IntelligenceItem(BaseModel):
    id: str
    title: str
    url: HttpUrl | str
    source: str
    source_type: SourceType = SourceType.other
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    topic: str = "general"
    summary: str = ""
    raw_text: str = ""
    authority_score: float = 0.5
    relevance_score: float = 0.0
    recency_score: float = 0.0
    novelty_score: float = 1.0
    risk_or_opportunity_score: float = 0.0
    duplication_penalty: float = 0.0
    final_score: float = 0.0
    evidence_quality_score: float = 0.0
    severity: str = "medium"
    urgency: str = "watch"
    risk_tags: list[str] = Field(default_factory=list)
    affected_domains: list[str] = Field(default_factory=list)
    evidence_level: EvidenceLevel = EvidenceLevel.unverified

    def to_json_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data["url"] = str(data["url"])
        return data
