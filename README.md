# RiskLens AI: Risk-Aware Market & Technology Intelligence Agent

[![tests](https://github.com/Justin-147/risklens-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/Justin-147/risklens-ai/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/Justin-147/risklens-ai?label=release)](https://github.com/Justin-147/risklens-ai/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Dashboard](https://img.shields.io/badge/dashboard-Streamlit-ff4b4b.svg)](README.md#run-the-dashboard)
[![Status](https://img.shields.io/badge/status-v0.2.0-green.svg)](CHANGELOG.md)
Current version: **V0.2.0**

RiskLens AI is a controlled, tool-using intelligence agent for public-source risk intelligence across financial services, FinTech/Web3 risk, and AI technology strategy.

It combines a deterministic risk intelligence pipeline with an auditable orchestration layer. The pipeline handles ingestion, normalization, deduplication, source reliability scoring, topic classification, risk tagging, evidence quality scoring, severity and urgency classification, ranking, and report generation. The agent layer adds profile-specific planning, tool selection, coverage evaluation, bounded retry behavior, lightweight memory, verification, and execution traces.

RiskLens AI is not investment advice. Not trading advice. Not legal, compliance, or financial advice.

## Coverage Areas

- Financial services, banking AI, wealth management, RegTech, and digital transformation
- FinTech, Web3, stablecoins, market structure, cybersecurity, liquidity, and reputation risk
- AI technology strategy, enterprise AI agents, model governance, AI safety, and infrastructure risk
- Public-source intelligence analysis, risk monitoring, and executive briefing generation

## Pipeline Mode vs Agent Mode

- `run`: deterministic pipeline mode. It collects or loads items, runs the risk intelligence pipeline, and generates English and Chinese reports.
- `agent-run`: controlled agent mode. It creates a profile-specific plan, selects tools, evaluates coverage gaps, retries within a fixed iteration limit, verifies evidence, writes memory, saves reports, and creates an execution trace.

## Architecture

```mermaid
flowchart TD
    A[Profile] --> B[Planner]
    B --> C[Tool Selector]
    C --> D1[RSS Tool]
    C --> D2[Regulatory Tool]
    C --> D3[arXiv Tool]
    C --> D4[Market Tool]
    C --> D5[USGS Tool]
    D1 --> E[Collected Items]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E
    E --> F[Normalize / Deduplicate / Score / Classify / Tag / Rank]
    F --> G[Coverage Evaluator]
    G -->|Gaps remain| C
    G -->|Enough evidence| H[Verifier]
    H --> I[Report Generator]
    I --> J[Markdown / HTML Brief]
    I --> K[Execution Trace]
    K --> L[Memory]
```

## Quick Start on Windows

Open PowerShell from the folder that contains `RiskLens_AI`.

```powershell
cd D:\CodexWork\RiskLens_AI
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m risklens.main validate
python -m risklens.main agent-run --profile financial_services --mock --as-of 2026-07-06 --output-root .tmp/demo
```

The `--as-of` value fixes report dates, filenames, and ranking recency. The `--output-root` value keeps runtime files under a disposable folder such as `.tmp/demo`.

## Common Commands

Run a deterministic mock pipeline:

```powershell
python -m risklens.main run --profile financial_services --mock --as-of 2026-07-06 --output-root .tmp/demo
```

Run controlled agent mode:

```powershell
python -m risklens.main agent-run --profile financial_services --mock --max-iterations 3 --as-of 2026-07-06 --output-root .tmp/demo
```

Run the gap/retry demo:

```powershell
python -m risklens.main agent-run --profile financial_services --mock --max-iterations 3 --simulate-gap --as-of 2026-07-06 --output-root .tmp/demo
```

Refresh curated sample artifacts:

```powershell
python -m risklens.main agent-run --profile financial_services --mock --max-iterations 3 --simulate-gap --as-of 2026-07-06 --output-root .tmp/sample-refresh --copy-samples
```

Run the complete local demo workflow:

```powershell
python scripts/run_demo.py
```

PowerShell wrapper:

```powershell
.\scripts\run_demo.ps1
```

## Local Verification

```powershell
ruff check .
python scripts/verify_line_endings.py
python -m compileall src tests scripts
mypy src/risklens
pytest
python -m risklens.main validate
python scripts/run_demo.py
python -m build
```

All checks should pass. The exact pytest count may change as validation coverage is added.

## Outputs

With `--output-root .tmp/demo`, runtime files are written under:

- `.tmp/demo/data/raw/`: collected raw candidates
- `.tmp/demo/data/processed/`: normalized, scored, tagged, and ranked items
- `.tmp/demo/data/memory/memory.json`: lightweight run, source, and item memory
- `.tmp/demo/reports/markdown/`: English and Chinese Markdown briefings
- `.tmp/demo/reports/html/`: English and Chinese HTML briefings
- `.tmp/demo/reports/traces/`: auditable agent execution traces

Curated examples are stored under:

- `examples/sample_reports/`
- `examples/sample_traces/`
- `examples/sample_outputs/`

Generated runtime folders such as `.tmp/`, `data/processed/`, `data/raw/`, `data/memory/`, `reports/`, `dist/`, and `build/` are intentionally ignored by Git.

## Execution Trace

The trace is an execution trace, not a hidden reasoning trace. It records the plan, tools called, coverage score, per-iteration coverage history, detected gaps, retry decisions, source mix, errors, and output paths.

The curated gap/retry example is:

```text
examples/sample_traces/financial_services_gap_trace.json
```

## Run the Dashboard

After generating at least one report:

```powershell
streamlit run src\risklens\dashboard\app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

Dashboard views:

- `Briefing`: processed items, source metadata, evidence quality, severity, urgency, final score, and English/Chinese report switching.
- `Agent Run Trace`: agent status, coverage history, plan topics, tools called, unresolved gaps, retry decisions, source mix, and generated report paths.

## Screenshots

### Dashboard Briefing View

![Dashboard Briefing](docs/screenshots/dashboard_briefing.png)

### Agent Run Trace View

![Agent Run Trace](docs/screenshots/agent_run_trace.png)

The Agent Run Trace screenshot shows a successful run. A separate curated gap/retry trace is available under `examples/sample_traces/financial_services_gap_trace.json` to demonstrate coverage gap detection and retry behavior.

## Demo Profiles

- `financial_services`: banking AI, wealth management, regulatory policy, operational resilience, model risk, and digital transformation.
- `fintech_web3_risk`: stablecoins, crypto market structure, regulation, cybersecurity, operational risk, liquidity risk, and reputational risk.
- `ai_technology_strategy`: model providers, AI agents, enterprise AI, AI infrastructure, model governance, AI safety, and technology risk.

## Scoring Formula

```text
final_score =
  0.24 * authority_score
+ 0.20 * relevance_score
+ 0.16 * recency_score
+ 0.12 * risk_or_opportunity_score
+ 0.10 * novelty_score
+ 0.10 * evidence_quality_score
+ 0.08 * severity_score
- duplication_penalty
```

Evidence quality is stored on each item. Severity is derived from rule-based severity labels (`low`, `medium`, `high`).

## Boundaries

- Not investment advice.
- Not trading advice.
- Not an automated trading tool.
- Not a fully autonomous agent.
- Does not process private or internal data.
- Mock data is synthetic demo data.
- Real mode depends on public source availability, RSS behavior, network access, and parser compatibility.

If public sources fail or coverage is incomplete, agent mode records the failure in the trace and can return `partial_success` with explicit coverage limitations.

## Optional LLM Mode

Mock mode is deterministic and does not require API keys. To use an OpenAI-compatible provider, copy `.env.example` to `.env`, set provider values, install the optional dependency, and run without `--mock`.

```powershell
python -m pip install -e ".[llm]"
copy .env.example .env
```

Then edit `.env`:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
RISKLENS_USE_LLM=true
```

## Project Files

- `LICENSE`: MIT License
- `CHANGELOG.md`: release history
- `.gitattributes`: LF line-ending policy
- `.github/workflows/tests.yml`: CI workflow for tests, linting, validation, CLI smoke runs, and package build

## Troubleshooting

If PowerShell blocks virtual environment activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\activate
```

If `python -m risklens.main ...` cannot find the package, run:

```powershell
python -m pip install -e ".[dev]"
```

If the dashboard shows no data, generate a report first with one of the `--mock` commands above.

## Release Status

Current release: `v0.2.0`.

RiskLens AI v0.2.0 is a controlled, auditable, public-source risk intelligence prototype. It supports deterministic pipeline mode, controlled agent mode, profile-specific planning, bounded retries, coverage evaluation, evidence verification, execution traces, English/Chinese reports, and a Streamlit dashboard.

This project is informational. It is not investment advice, trading advice, legal advice, compliance advice, financial advice, a real-money trading system, or a fully autonomous agent.
