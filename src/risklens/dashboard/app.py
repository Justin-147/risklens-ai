from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from risklens.dashboard.file_matching import processed_files_for_profile, report_path_for_processed

ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports" / "markdown"
TRACES = ROOT / "reports" / "traces"

st.set_page_config(page_title="RiskLens AI", layout="wide")
st.title("RiskLens AI")

tab_report, tab_trace = st.tabs(["Briefing", "Agent Run Trace"])

with tab_report:
    profiles = ["financial_services", "fintech_web3_risk", "ai_technology_strategy"]
    profile = st.sidebar.selectbox("Profile", profiles)
    mode = st.sidebar.selectbox("Mode", ["All", "Pipeline", "Agent"])
    language = st.sidebar.radio("Language", ["English", "涓枃"], horizontal=True)
    language_suffix = "zh" if language == "涓枃" else "en"

    files = processed_files_for_profile(PROCESSED, profile, mode=mode)
    if not files:
        st.info("No processed report data yet. Run: python -m risklens.main agent-run --profile financial_services --mock")
    else:
        selected = st.sidebar.selectbox("Run", files, format_func=lambda path: path.name)
        items = json.loads(selected.read_text(encoding="utf-8"))
        df = pd.DataFrame(items)

        st.metric("Signals", len(df))
        chart_col1, chart_col2 = st.columns(2)
        if "source_type" in df.columns:
            chart_col1.subheader("Source Type Distribution")
            chart_col1.bar_chart(df["source_type"].value_counts())
        if "severity" in df.columns:
            chart_col2.subheader("Severity Distribution")
            chart_col2.bar_chart(df["severity"].value_counts())

        display_columns = [column for column in ["title", "source", "source_type", "evidence_level", "evidence_quality_score", "severity", "urgency", "final_score", "risk_tags", "url"] if column in df.columns]
        st.dataframe(df[display_columns], width="stretch", hide_index=True)

        report_file = report_path_for_processed(REPORTS, selected, language_suffix)
        if report_file.exists():
            st.markdown(report_file.read_text(encoding="utf-8"))
        else:
            st.warning(f"No {language} report found for this run. Regenerate the report with the latest pipeline.")

with tab_trace:
    trace_files = sorted(TRACES.glob("*_trace.json"), reverse=True)
    if not trace_files:
        st.info("No agent traces yet. Run: python -m risklens.main agent-run --profile financial_services --mock")
    else:
        selected_trace = st.selectbox("Trace", trace_files, format_func=lambda path: path.name)
        trace = json.loads(selected_trace.read_text(encoding="utf-8"))
        col1, col2, col3 = st.columns(3)
        col1.metric("Profile", trace.get("profile", ""))
        col2.metric("Status", trace.get("status", ""))
        col3.metric("Coverage", f"{trace.get('coverage_score', 0):.2f}")
        st.metric("Iterations", trace.get("iteration_count", 0))

        history = trace.get("coverage_history", [])
        if history:
            st.subheader("Coverage History")
            history_df = pd.DataFrame(history)
            st.line_chart(history_df.set_index("iteration")["coverage_score"])
            st.dataframe(history_df, width="stretch", hide_index=True)

        plan = trace.get("plan") or {}
        st.subheader("Plan")
        st.write("Required topics", plan.get("required_topics", []))
        st.write("Required tools", plan.get("required_tools", []))

        st.subheader("Tools Called")
        st.dataframe(pd.DataFrame(trace.get("tools_called", [])), width="stretch", hide_index=True)

        st.subheader("Unresolved Gaps")
        st.write(trace.get("gaps", []))

        st.subheader("Retry Decisions")
        st.write(trace.get("retry_decisions", []))

        st.subheader("Source Mix")
        st.write(trace.get("source_mix", {}))

        st.subheader("Generated Reports")
        st.write(trace.get("final_report_paths", {}))