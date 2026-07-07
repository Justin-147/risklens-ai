from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Protocol

from risklens.agent.config import get_agent_profile
from risklens.agent.state import TaskStatus, ToolResult
from risklens.fetchers.arxiv_fetcher import fetch_arxiv
from risklens.fetchers.market_fetcher import fetch_market_signals
from risklens.fetchers.regulatory_fetcher import fetch_regulatory
from risklens.fetchers.rss_fetcher import fetch_rss
from risklens.fetchers.usgs_fetcher import fetch_usgs_events
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType


class AgentTool(Protocol):
    name: str

    def run(self, profile: str, parameters: dict | None = None) -> ToolResult: ...


def _source_type(value: str) -> SourceType:
    aliases = {
        "high_quality_media": SourceType.media,
        "cybersecurity_source": SourceType.media,
        "scientific_source": SourceType.official,
    }
    return aliases.get(
        value, SourceType(value) if value in SourceType._value2member_map_ else SourceType.other
    )


def _evidence_level(value: str) -> EvidenceLevel:
    return (
        EvidenceLevel(value)
        if value in EvidenceLevel._value2member_map_
        else EvidenceLevel.unverified
    )


def _metadata(tool_name: str, items: list[IntelligenceItem], elapsed: float) -> dict:
    return {
        "item_count": len(items),
        "source_count": len({item.source for item in items}),
        "elapsed_seconds": round(elapsed, 3),
        "tool_name": tool_name,
    }


def _generated_at(parameters: dict | None = None) -> datetime:
    value = (parameters or {}).get("generated_at")
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return datetime.now(UTC)


def synthetic_items_for_tool(
    profile: str,
    tool_name: str,
    omit_source_types: set[str] | None = None,
    generated_at: datetime | None = None,
) -> list[IntelligenceItem]:
    profile_config = get_agent_profile(profile)
    rows = profile_config.get("synthetic_items", {}).get(tool_name, [])
    omit_source_types = omit_source_types or set()
    published_at = generated_at or datetime.now(UTC)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    else:
        published_at = published_at.astimezone(UTC)
    items: list[IntelligenceItem] = []
    for index, row in enumerate(rows, start=1):
        source_type_value = str(row.get("source_type", "other"))
        if source_type_value in omit_source_types:
            continue
        summary = str(row.get("summary", "Synthetic RiskLens demo signal."))
        items.append(
            IntelligenceItem(
                id=f"synthetic-{tool_name}-{profile}-{index}",
                title=str(row.get("title", f"Synthetic {tool_name} signal {index}")),
                url=str(
                    row.get(
                        "url", f"https://example.org/risklens-demo/{profile}/{tool_name}/{index}"
                    )
                ),
                source=str(row.get("source", "Synthetic Source")),
                source_type=_source_type(source_type_value),
                published_at=published_at,
                summary=summary,
                raw_text=summary,
                evidence_level=_evidence_level(str(row.get("evidence_level", "secondary"))),
            )
        )
    return items


class BaseTool:
    name = "base_tool"

    def __init__(self, mock: bool = False, simulate_gap: bool = False) -> None:
        self.mock = mock
        self.simulate_gap = simulate_gap

    def run(self, profile: str, parameters: dict | None = None) -> ToolResult:
        started = time.perf_counter()
        try:
            items = self._run(profile, parameters or {})
            elapsed = time.perf_counter() - started
            status = TaskStatus.SUCCESS if items else TaskStatus.PARTIAL_SUCCESS
            errors = [] if items else ["Tool returned no items."]
            return ToolResult(
                tool_name=self.name,
                status=status,
                items=items,
                errors=errors,
                metadata=_metadata(self.name, items, elapsed),
            )
        except Exception as exc:  # pragma: no cover - depends on network/parser behavior
            elapsed = time.perf_counter() - started
            return ToolResult(
                tool_name=self.name,
                status=TaskStatus.FAILED,
                items=[],
                errors=[str(exc)],
                metadata={"elapsed_seconds": round(elapsed, 3), "item_count": 0, "source_count": 0},
            )

    def _run(self, profile: str, parameters: dict) -> list[IntelligenceItem]:
        raise NotImplementedError


class RSSFetcherTool(BaseTool):
    name = "rss_fetcher_tool"

    def _run(self, profile: str, parameters: dict) -> list[IntelligenceItem]:
        if self.mock:
            return synthetic_items_for_tool(
                profile,
                self.name,
                set(parameters.get("omit_source_types", [])),
                _generated_at(parameters),
            )
        items: list[IntelligenceItem] = []
        for feed in get_agent_profile(profile).get("feeds", {}).get("rss", []):
            items.extend(fetch_rss(feed["url"], feed["source"], limit=parameters.get("limit", 5)))
        return items


class ArxivFetcherTool(BaseTool):
    name = "arxiv_fetcher_tool"

    def _run(self, profile: str, parameters: dict) -> list[IntelligenceItem]:
        if self.mock:
            return synthetic_items_for_tool(
                profile,
                self.name,
                set(parameters.get("omit_source_types", [])),
                _generated_at(parameters),
            )
        items: list[IntelligenceItem] = []
        for query in (
            get_agent_profile(profile).get("queries", {}).get("arxiv", [profile.replace("_", " ")])
        ):
            fetched = fetch_arxiv(query, limit=parameters.get("limit", 3))
            for item in fetched:
                item.source_type = SourceType.academic
                item.evidence_level = EvidenceLevel.secondary
            items.extend(fetched)
        return items


class RegulatoryFetcherTool(BaseTool):
    name = "regulatory_fetcher_tool"

    def _run(self, profile: str, parameters: dict) -> list[IntelligenceItem]:
        if self.mock:
            return synthetic_items_for_tool(
                profile,
                self.name,
                set(parameters.get("omit_source_types", [])),
                _generated_at(parameters),
            )
        items: list[IntelligenceItem] = []
        for feed in get_agent_profile(profile).get("feeds", {}).get("regulatory", []):
            fetched = fetch_regulatory(
                feed["url"], feed["source"], limit=parameters.get("limit", 5)
            )
            for item in fetched:
                item.source_type = SourceType.regulatory
                item.evidence_level = EvidenceLevel.primary
            items.extend(fetched)
        return items


class MarketFetcherTool(BaseTool):
    name = "market_fetcher_tool"

    def _run(self, profile: str, parameters: dict) -> list[IntelligenceItem]:
        if self.mock:
            return synthetic_items_for_tool(
                profile,
                self.name,
                set(parameters.get("omit_source_types", [])),
                _generated_at(parameters),
            )
        rows = fetch_market_signals()
        items: list[IntelligenceItem] = []
        for idx, row in enumerate(rows, start=1):
            summary = str(
                row.get("summary")
                or row.get("description")
                or "Public market signal collected by market adapter."
            )
            items.append(
                IntelligenceItem(
                    id=f"market-{profile}-{idx}",
                    title=str(row.get("title") or row.get("name") or f"Market signal {idx}"),
                    url=str(row.get("url") or "https://example.org/risklens-demo/market-signal"),
                    source=str(row.get("source") or "Market Adapter"),
                    source_type=SourceType.market,
                    published_at=_generated_at(parameters),
                    summary=summary,
                    raw_text=summary,
                    evidence_level=EvidenceLevel.secondary,
                )
            )
        return items


class USGSFetcherTool(BaseTool):
    name = "usgs_fetcher_tool"

    def _run(self, profile: str, parameters: dict) -> list[IntelligenceItem]:
        if self.mock:
            return synthetic_items_for_tool(
                profile,
                self.name,
                set(parameters.get("omit_source_types", [])),
                _generated_at(parameters),
            )
        rows = fetch_usgs_events()
        items: list[IntelligenceItem] = []
        for idx, row in enumerate(rows, start=1):
            summary = str(
                row.get("summary") or row.get("place") or "USGS public scientific signal."
            )
            items.append(
                IntelligenceItem(
                    id=f"usgs-{idx}",
                    title=str(row.get("title") or row.get("place") or f"USGS event {idx}"),
                    url=str(row.get("url") or "https://earthquake.usgs.gov/"),
                    source="USGS",
                    source_type=SourceType.official,
                    published_at=_generated_at(parameters),
                    summary=summary,
                    raw_text=summary,
                    evidence_level=EvidenceLevel.primary,
                )
            )
        return items


def build_tool_registry(mock: bool = False, simulate_gap: bool = False) -> dict[str, BaseTool]:
    tools = [
        RSSFetcherTool(mock, simulate_gap),
        ArxivFetcherTool(mock, simulate_gap),
        RegulatoryFetcherTool(mock, simulate_gap),
        MarketFetcherTool(mock, simulate_gap),
        USGSFetcherTool(mock, simulate_gap),
    ]
    return {tool.name: tool for tool in tools}
