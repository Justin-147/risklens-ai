from __future__ import annotations

from risklens.agent.config import get_agent_profile, load_agent_config
from risklens.agent.state import IntelligencePlan


def available_profiles() -> list[str]:
    return sorted(load_agent_config().get("profiles", {}).keys())


def create_plan(profile: str, max_iterations: int = 3, max_items: int = 8) -> IntelligencePlan:
    data = get_agent_profile(profile)
    return IntelligencePlan(
        profile=profile,
        required_topics=list(data.get("required_topics", [])),
        preferred_source_types=list(data.get("preferred_source_types", [])),
        required_tools=list(data.get("required_tools", [])),
        min_items=max_items,
        max_iterations=max_iterations,
    )
