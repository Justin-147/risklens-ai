from __future__ import annotations

from pathlib import Path


def processed_files_for_profile(processed_dir: Path, profile: str, mode: str = "All") -> list[Path]:
    pipeline_files = sorted(processed_dir.glob(f"*_{profile}.json"), reverse=True)
    agent_files = sorted(processed_dir.glob(f"*_{profile}_agent.json"), reverse=True)
    if mode == "Pipeline":
        return [path for path in pipeline_files if not path.name.endswith("_agent.json")]
    if mode == "Agent":
        return agent_files
    combined = {path.name: path for path in pipeline_files + agent_files}
    return sorted(combined.values(), reverse=True)


def report_path_for_processed(report_dir: Path, processed_file: Path, language_suffix: str) -> Path:
    return report_dir / processed_file.name.replace(".json", f"_{language_suffix}.md")