from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from risklens.models import IntelligenceItem


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    RETRYING = "retrying"
    PARTIAL_SUCCESS = "partial_success"
    SUCCESS = "success"
    FAILED = "failed"


class IntelligencePlan(BaseModel):
    profile: str
    required_topics: list[str]
    preferred_source_types: list[str]
    required_tools: list[str]
    min_items: int = 8
    max_iterations: int = 3
    source_diversity_constraints: dict[str, float] = Field(
        default_factory=lambda: {"max_single_source_share": 0.30}
    )


class ToolCall(BaseModel):
    tool_name: str
    reason: str
    iteration: int
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_name: str
    status: TaskStatus
    items: list[IntelligenceItem] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CoverageEvaluation(BaseModel):
    coverage_score: float
    missing_topics: list[str] = Field(default_factory=list)
    source_diversity_issues: list[str] = Field(default_factory=list)
    evidence_quality_issues: list[str] = Field(default_factory=list)
    recommended_next_tools: list[str] = Field(default_factory=list)
    should_continue: bool = False


class AgentRunState(BaseModel):
    run_id: str
    profile: str
    status: TaskStatus = TaskStatus.PENDING
    plan: IntelligencePlan | None = None
    iteration_count: int = 0
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    collected_items: list[IntelligenceItem] = Field(default_factory=list)
    processed_items: list[IntelligenceItem] = Field(default_factory=list)
    evaluations: list[CoverageEvaluation] = Field(default_factory=list)
    retry_decisions: list[str] = Field(default_factory=list)
    final_report_paths: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
