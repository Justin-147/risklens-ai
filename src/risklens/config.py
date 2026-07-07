from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_profiles() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "demo_profiles.yaml")


def load_taxonomy() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "risk_taxonomy.yaml")


def load_sources() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "sources.yaml")
