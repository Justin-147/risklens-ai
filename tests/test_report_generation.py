from risklens.llm.mock_provider import MockLLMProvider
from risklens.main import mock_items
from risklens.pipeline.build_context import build_report_context


def test_mock_report_contains_required_sections():
    context = build_report_context("Financial Services", mock_items("financial_services"))
    report = MockLLMProvider().generate_report(context)
    assert "## Executive Summary" in report
    assert "## Key Signals" in report
    assert "Fact:" in report
    assert "Assessment:" in report
    assert "Why it matters:" in report


def test_mock_report_can_generate_chinese_version():
    context = build_report_context("Financial Services", mock_items("financial_services"))
    report = MockLLMProvider().generate_report(context, language="zh")
    assert "## 执行摘要" in report
    assert "## 关键信号" in report
    assert "事实：" in report
    assert "评估：" in report