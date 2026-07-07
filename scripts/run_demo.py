from __future__ import annotations

import subprocess
import sys

COMMANDS = [
    [sys.executable, "-m", "ruff", "check", "."],
    [sys.executable, "scripts/verify_line_endings.py"],
    [sys.executable, "-m", "compileall", "src", "tests", "scripts"],
    [sys.executable, "-m", "mypy", "src/risklens"],
    [sys.executable, "-m", "pytest"],
    [sys.executable, "-m", "risklens.main", "validate"],
    [
        sys.executable,
        "-m",
        "risklens.main",
        "run",
        "--profile",
        "financial_services",
        "--mock",
        "--as-of",
        "2026-07-06",
        "--output-root",
        ".tmp/demo",
    ],
    [
        sys.executable,
        "-m",
        "risklens.main",
        "agent-run",
        "--profile",
        "financial_services",
        "--mock",
        "--max-iterations",
        "3",
        "--simulate-gap",
        "--as-of",
        "2026-07-06",
        "--output-root",
        ".tmp/demo",
    ],
    [
        sys.executable,
        "-m",
        "risklens.main",
        "agent-run",
        "--profile",
        "ai_technology_strategy",
        "--mock",
        "--max-iterations",
        "3",
        "--as-of",
        "2026-07-06",
        "--output-root",
        ".tmp/demo",
    ],
    [
        sys.executable,
        "-m",
        "risklens.main",
        "agent-run",
        "--profile",
        "fintech_web3_risk",
        "--mock",
        "--max-iterations",
        "3",
        "--as-of",
        "2026-07-06",
        "--output-root",
        ".tmp/demo",
    ],
    [sys.executable, "-m", "build"],
]


def main() -> int:
    for command in COMMANDS:
        print("+ " + " ".join(command))
        subprocess.run(command, check=True)
    print("demo_status=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
