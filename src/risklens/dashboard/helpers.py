from __future__ import annotations

import pandas as pd


def language_suffix(language: str) -> str:
    return "zh" if language == "中文" else "en"


def trace_frame(trace: dict) -> pd.DataFrame:
    return pd.DataFrame(trace.get("coverage_history", []))


def source_mix_frame(trace: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [{"source": key, "count": value} for key, value in trace.get("source_mix", {}).items()]
    )
