from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from risklens.agent.state import AgentRunState, CoverageEvaluation, ToolResult
from risklens.config import DATA_DIR
from risklens.models import IntelligenceItem

MEMORY_PATH = DATA_DIR / "memory" / "memory.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


class JsonMemoryStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or MEMORY_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"runs": [], "sources": {}, "items": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_run(self, state: AgentRunState, started_at: str, completed_at: str) -> None:
        data = self.load()
        latest_eval: CoverageEvaluation | None = (
            state.evaluations[-1] if state.evaluations else None
        )
        gaps = []
        if latest_eval:
            gaps.extend(latest_eval.missing_topics)
            gaps.extend(latest_eval.source_diversity_issues)
            gaps.extend(latest_eval.evidence_quality_issues)
        data["runs"].append(
            {
                "run_id": state.run_id,
                "profile": state.profile,
                "started_at": started_at,
                "completed_at": completed_at,
                "final_status": state.status.value,
                "coverage_score": latest_eval.coverage_score if latest_eval else 0.0,
                "item_count": len(state.processed_items),
                "gaps": gaps,
                "report_paths": state.final_report_paths,
            }
        )
        self._record_sources(data, state.tool_results)
        self._record_items(data, state.processed_items)
        self.save(data)

    def _record_sources(self, data: dict[str, Any], results: list[ToolResult]) -> None:
        sources = data.setdefault("sources", {})
        for result in results:
            source_names = {item.source for item in result.items} or {result.tool_name}
            for source in source_names:
                entry = sources.setdefault(
                    source,
                    {
                        "tool_name": result.tool_name,
                        "success_count": 0,
                        "failure_count": 0,
                        "last_success_at": None,
                        "last_error": None,
                        "average_item_count": 0.0,
                    },
                )
                if result.items:
                    entry["success_count"] += 1
                    entry["last_success_at"] = _now()
                    total_success = entry["success_count"]
                    entry["average_item_count"] = round(
                        ((entry["average_item_count"] * (total_success - 1)) + len(result.items))
                        / total_success,
                        2,
                    )
                else:
                    entry["failure_count"] += 1
                    entry["last_error"] = "; ".join(result.errors)

    def _record_items(self, data: dict[str, Any], items: list[IntelligenceItem]) -> None:
        item_history = data.setdefault("items", {})
        now = _now()
        for item in items:
            key = _hash(str(item.url) + item.title)
            entry = item_history.setdefault(
                key,
                {
                    "url_hash": _hash(str(item.url)),
                    "title_hash": _hash(item.title),
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "selected_in_report_count": 0,
                },
            )
            entry["last_seen_at"] = now
            entry["selected_in_report_count"] += 1
