from __future__ import annotations

from functools import lru_cache
from typing import Any

from risklens.config import CONFIG_DIR, load_yaml


@lru_cache(maxsize=1)
def load_agent_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "agent_plans.yaml")


def get_agent_profile(profile: str) -> dict[str, Any]:
    profiles = load_agent_config().get("profiles", {})
    if profile not in profiles:
        raise ValueError(f"Unknown agent profile: {profile}")
    return profiles[profile]