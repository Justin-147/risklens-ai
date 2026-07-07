from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from risklens.agent.tools import build_tool_registry
from risklens.config import CONFIG_DIR, PROJECT_ROOT, load_yaml
from risklens.models import EvidenceLevel, SourceType


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "failed" if self.errors else "passed"


def _profiles_from_demo(data: dict[str, Any]) -> dict[str, Any]:
    profiles = data.get("profiles")
    if isinstance(profiles, dict):
        return profiles
    return data


def _is_http_url(value: object) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _check_path(path: Path, label: str, result: ValidationResult) -> None:
    if not path.exists():
        result.errors.append(f"Missing {label}: {path.relative_to(PROJECT_ROOT)}")


def _validate_demo_profiles(result: ValidationResult) -> dict[str, Any]:
    path = CONFIG_DIR / "demo_profiles.yaml"
    _check_path(path, "demo_profiles.yaml", result)
    if not path.exists():
        return {}
    profiles = _profiles_from_demo(load_yaml(path))
    if not profiles:
        result.errors.append("demo_profiles.yaml must define at least one profile.")
    return profiles


def _validate_taxonomy(result: ValidationResult) -> None:
    path = CONFIG_DIR / "risk_taxonomy.yaml"
    _check_path(path, "risk_taxonomy.yaml", result)
    if not path.exists():
        return
    data = load_yaml(path)
    tags = data.get("risk_tags", {})
    if not isinstance(tags, dict) or not tags:
        result.errors.append("risk_taxonomy.yaml must define risk_tags.")
        return
    for tag, config in tags.items():
        terms = config.get("terms") if isinstance(config, dict) else None
        description = config.get("description") if isinstance(config, dict) else None
        if not terms and not description:
            result.errors.append(f"Risk tag '{tag}' must define terms or description.")


def _validate_agent_plans(demo_profiles: dict[str, Any], result: ValidationResult) -> None:
    path = CONFIG_DIR / "agent_plans.yaml"
    _check_path(path, "agent_plans.yaml", result)
    if not path.exists():
        return
    data = load_yaml(path)
    profiles = data.get("profiles", {})
    if not isinstance(profiles, dict) or not profiles:
        result.errors.append("agent_plans.yaml must define profiles.")
        return

    registry = build_tool_registry(mock=True)
    valid_tools = set(registry)
    valid_source_types = {item.value for item in SourceType}
    valid_evidence_levels = {item.value for item in EvidenceLevel}

    for profile_name in demo_profiles:
        if profile_name not in profiles:
            result.errors.append(f"agent_plans.yaml missing profile '{profile_name}'.")

    for profile_name, profile in profiles.items():
        for key in ["required_topics", "preferred_source_types", "required_tools"]:
            if not profile.get(key):
                result.errors.append(f"Profile '{profile_name}' must define {key}.")

        for tool_name in profile.get("required_tools", []):
            if tool_name not in valid_tools:
                result.errors.append(
                    f"Profile '{profile_name}' references unknown required tool '{tool_name}'."
                )

        synthetic_items = profile.get("synthetic_items", {})
        for tool_name, rows in synthetic_items.items():
            if tool_name not in valid_tools:
                result.errors.append(
                    f"Profile '{profile_name}' has synthetic items for unknown tool '{tool_name}'."
                )
            for index, row in enumerate(rows, start=1):
                prefix = f"Profile '{profile_name}' synthetic item {tool_name}[{index}]"
                for key in ["title", "source", "summary", "url"]:
                    if not row.get(key):
                        result.errors.append(f"{prefix} missing {key}.")
                source_type = str(row.get("source_type", "other"))
                if source_type not in valid_source_types:
                    result.errors.append(f"{prefix} has invalid source_type '{source_type}'.")
                evidence_level = str(row.get("evidence_level", "unverified"))
                if evidence_level not in valid_evidence_levels:
                    result.errors.append(f"{prefix} has invalid evidence_level '{evidence_level}'.")
                if not _is_http_url(row.get("url")):
                    result.errors.append(f"{prefix} url must start with http:// or https://.")


def _validate_examples(result: ValidationResult) -> None:
    expected = [
        PROJECT_ROOT / "examples" / "sample_reports" / "financial_services_agent_en.md",
        PROJECT_ROOT / "examples" / "sample_reports" / "financial_services_agent_zh.md",
        PROJECT_ROOT / "examples" / "sample_reports" / "fintech_web3_risk_agent_en.md",
        PROJECT_ROOT / "examples" / "sample_reports" / "ai_technology_strategy_agent_en.md",
        PROJECT_ROOT / "examples" / "sample_traces" / "financial_services_gap_trace.json",
        PROJECT_ROOT / "examples" / "sample_outputs" / "financial_services_agent.json",
    ]
    for path in expected:
        _check_path(path, "sample output example", result)


def _validate_readme(result: ValidationResult) -> None:
    readme = PROJECT_ROOT / "README.md"
    _check_path(readme, "README.md", result)
    if not readme.exists():
        return
    text = readme.read_text(encoding="utf-8").lower()
    required_fragments = ["not investment advice", "not trading advice"]
    for fragment in required_fragments:
        if fragment not in text:
            result.errors.append(f"README.md must include disclaimer fragment: {fragment}")


def validate_project() -> ValidationResult:
    result = ValidationResult()
    demo_profiles = _validate_demo_profiles(result)
    _validate_taxonomy(result)
    _validate_agent_plans(demo_profiles, result)
    _validate_examples(result)
    _validate_readme(result)
    return result
