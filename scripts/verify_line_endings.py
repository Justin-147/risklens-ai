from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKED_FILES = [
    "README.md",
    "README.zh-CN.md",
    "CHANGELOG.md",
    "LICENSE",
    "pyproject.toml",
    ".gitattributes",
    ".github/workflows/tests.yml",
    "src/risklens/main.py",
    "src/risklens/models.py",
    "src/risklens/agent/orchestrator.py",
    "src/risklens/agent/evaluator.py",
    "src/risklens/agent/verifier.py",
    "src/risklens/llm/mock_provider.py",
    "src/risklens/writers/html_writer.py",
    "src/risklens/writers/formatting.py",
    "src/risklens/dashboard/app.py",
    "tests/test_report_generation.py",
    "tests/test_report_safety.py",
    "tests/test_agent_v2.py",
    "scripts/run_demo.py",
    "scripts/run_demo.ps1",
]

TEXT_SUFFIXES_FOR_LITERAL_CHECK = {
    "",
    ".gitignore",
    ".json",
    ".md",
    ".ps1",
    ".toml",
    ".yaml",
    ".yml",
}


def _is_text_artifact(path: Path) -> bool:
    return path.name == ".gitattributes" or path.suffix in TEXT_SUFFIXES_FOR_LITERAL_CHECK


def main() -> int:
    failures: list[str] = []
    for relative in CHECKED_FILES:
        path = ROOT / relative
        if not path.exists():
            failures.append(f"missing_file={relative}")
            continue
        content = path.read_bytes()
        if b"\r" in content:
            failures.append(f"non_lf_line_ending={relative}")
        if content.count(b"\n") == 0:
            failures.append(f"no_lf_line_ending={relative}")
        if _is_text_artifact(path) and (b"`r`n" in content or b"\\r\\n" in content):
            failures.append(f"literal_escape_artifact={relative}")

    if failures:
        for failure in failures:
            print(failure)
        return 1
    print("line_ending_status=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
