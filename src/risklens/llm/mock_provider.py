from __future__ import annotations

from datetime import UTC, datetime

from risklens.llm.provider import LLMProvider
from risklens.writers.formatting import md_cell, safe_text, safe_url


class MockLLMProvider(LLMProvider):
    def generate_report(self, context: dict, language: str = "en") -> str:
        language = language if language in {"en", "zh"} else "en"
        if language == "zh":
            return self._generate_zh_report(context)
        return self._generate_en_report(context)

    def _report_date(self, context: dict) -> str:
        return safe_text(context.get("report_date") or datetime.now(UTC).date().isoformat())

    def _score(self, item: dict, key: str) -> str:
        try:
            return f"{float(item.get(key, 0.0)):.2f}"
        except (TypeError, ValueError):
            return "0.00"

    def _tags(self, item: dict) -> str:
        return ", ".join(safe_text(tag) for tag in item.get("risk_tags", []))

    def _confidence(self, item: dict, language: str = "en") -> str:
        score = item.get("authority_score", 0.0)
        if score >= 0.85:
            return "高" if language == "zh" else "High"
        if score >= 0.65:
            return "中" if language == "zh" else "Medium"
        return "低" if language == "zh" else "Low"

    def _generate_en_report(self, context: dict) -> str:
        items = context["items"]
        profile_name = safe_text(context["profile_name"])
        today = self._report_date(context)
        lines = [
            f"# RiskLens AI Brief | {today} | {profile_name}",
            "",
            "## Executive Summary",
            self._english_summary_bullet(profile_name, 1),
            self._english_summary_bullet(profile_name, 2),
            "- No buy/sell investment recommendations are provided; this briefing supports "
            "strategy, risk, and transformation review.",
            "",
            "## Key Signals",
            "| Signal | Source | Source Type | Evidence Level | Risk Tag | Severity | "
            "Urgency | Confidence | Evidence Quality Score | Impact |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for item in items:
            tags = self._tags(item)
            lines.append(
                f"| {md_cell(item['title'])} | {md_cell(item['source'])} | "
                f"{md_cell(item['source_type'])} | {md_cell(item['evidence_level'])} | "
                f"{md_cell(tags)} | {md_cell(item.get('severity', 'medium'))} | "
                f"{md_cell(item.get('urgency', 'watch'))} | {md_cell(self._confidence(item))} | "
                f"{md_cell(self._score(item, 'evidence_quality_score'))} | "
                f"{md_cell(item['summary'])} |"
            )

        lines.extend(["", "## Analysis by Theme"])
        for item in items:
            tags = self._tags(item)
            lines.extend(
                [
                    f"### {safe_text(item['title'])}",
                    f"- Fact: {safe_text(item['summary'])} Source: {safe_text(item['source'])} "
                    f"({safe_text(item['published_at'])}) {safe_url(item['url'])}",
                    "- Assessment: Risk interpretation: Primary tags are "
                    f"{safe_text(tags)}; severity is {safe_text(item.get('severity', 'medium'))} "
                    f"and urgency is {safe_text(item.get('urgency', 'watch'))}.",
                    self._english_why_it_matters(profile_name),
                    self._english_monitoring_action(item),
                    "",
                ]
            )

        lines.extend(
            [
                "## Risk & Opportunity Tags",
                ", ".join(safe_text(tag) for tag in context["top_risks"]),
                "",
                "## Actionable Insights",
                self._english_action("strategy"),
                self._english_action("risk"),
                self._english_action("ai"),
                "",
                "## Source List",
            ]
        )
        for item in items:
            lines.append(
                f"- {safe_text(item['title'])} | {safe_text(item['source'])} | "
                f"{safe_text(item['published_at'])} | {safe_url(item['url'])}"
            )
        return "\n".join(lines)

    def _generate_zh_report(self, context: dict) -> str:
        items = context["items"]
        profile_name = safe_text(context["profile_name"])
        today = self._report_date(context)
        lines = [
            f"# RiskLens AI 简报 | {today} | {profile_name}",
            "",
            "## 执行摘要",
            self._chinese_summary_bullet(profile_name, 1),
            self._chinese_summary_bullet(profile_name, 2),
            "- 本简报不提供买入/卖出投资建议，仅用于支持战略、风险和转型分析。",
            "",
            "## 关键信号",
            "| 信号 | 来源 | 来源类型 | 证据等级 | 风险标签 | 严重性 | 紧迫性 | "
            "置信度 | 证据质量评分 | 影响 |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for item in items:
            tags = self._tags(item)
            lines.append(
                f"| {md_cell(item['title'])} | {md_cell(item['source'])} | "
                f"{md_cell(item['source_type'])} | {md_cell(item['evidence_level'])} | "
                f"{md_cell(tags)} | {md_cell(item.get('severity', 'medium'))} | "
                f"{md_cell(item.get('urgency', 'watch'))} | "
                f"{md_cell(self._confidence(item, 'zh'))} | "
                f"{md_cell(self._score(item, 'evidence_quality_score'))} | "
                f"{md_cell(item['summary'])} |"
            )

        lines.extend(["", "## 按主题分析"])
        for item in items:
            tags = self._tags(item)
            lines.extend(
                [
                    f"### {safe_text(item['title'])}",
                    f"- 事实：{safe_text(item['summary'])} 来源：{safe_text(item['source'])}"
                    f"（{safe_text(item['published_at'])}）{safe_url(item['url'])}",
                    f"- 评估：风险解读：主要标签为 {safe_text(tags)}；"
                    f"严重性为 {safe_text(item.get('severity', 'medium'))}，"
                    f"紧迫性为 {safe_text(item.get('urgency', 'watch'))}。",
                    self._chinese_why_it_matters(profile_name),
                    self._chinese_monitoring_action(item),
                    "",
                ]
            )

        lines.extend(
            [
                "## 风险与机会标签",
                ", ".join(safe_text(tag) for tag in context["top_risks"]),
                "",
                "## 可行动洞察",
                self._chinese_action("strategy"),
                self._chinese_action("risk"),
                self._chinese_action("ai"),
                "",
                "## 来源列表",
            ]
        )
        for item in items:
            lines.append(
                f"- {safe_text(item['title'])} | {safe_text(item['source'])} | "
                f"{safe_text(item['published_at'])} | {safe_url(item['url'])}"
            )
        return "\n".join(lines)

    def _profile_kind(self, profile_name: str) -> str:
        lowered = profile_name.lower()
        if "web3" in lowered or "fintech" in lowered:
            return "web3"
        if "technology" in lowered or "ai" in lowered:
            return "ai"
        return "financial"

    def _english_summary_bullet(self, profile_name: str, index: int) -> str:
        kind = self._profile_kind(profile_name)
        bullets = {
            "financial": [
                "- Signals point to tighter expectations for third-party AI risk, model "
                "governance, operational resilience, and controlled transformation.",
                "- Wealth management and banking AI use cases require stronger auditability, "
                "human oversight, and supervisory evidence trails.",
            ],
            "web3": [
                "- Signals concentrate around stablecoin reserves, custody controls, "
                "enforcement, liquidity stress, and reputational exposure.",
                "- Market structure and cyber-risk signals suggest monitoring disclosure, "
                "segregation, incident response, and customer trust.",
            ],
            "ai": [
                "- Signals show enterprise AI moving toward governed agent deployments, "
                "model evaluation discipline, and AI safety controls.",
                "- Infrastructure cost volatility and platform dependency remain key risks "
                "for scaling AI systems.",
            ],
        }
        return bullets[kind][index - 1]

    def _chinese_summary_bullet(self, profile_name: str, index: int) -> str:
        kind = self._profile_kind(profile_name)
        bullets = {
            "financial": [
                "- 信号显示，第三方 AI 风险、模型治理、运营韧性和可控数字化转型的重要性正在上升。",
                "- 财富管理和银行 AI 场景需要更强的可审计性、人工监督和监管证据链。",
            ],
            "web3": [
                "- 信号集中在稳定币储备透明度、托管控制、监管执法、流动性压力和声誉风险。",
                "- 市场结构和网络风险信号显示，监控重点应放在披露、资产隔离、事件响应和客户信任。",
            ],
            "ai": [
                "- 信号显示，企业 AI 正从试点走向受治理的 agent 部署、模型评估和 AI safety 控制。",
                "- 基础设施成本波动和平台依赖仍是 AI 系统规模化时的重要技术战略风险。",
            ],
        }
        return bullets[kind][index - 1]

    def _english_why_it_matters(self, profile_name: str) -> str:
        kind = self._profile_kind(profile_name)
        if kind == "web3":
            return (
                "- Why it matters: FinTech and Web3 teams can translate this into reserve, "
                "custody, cyber, liquidity, and reputational monitoring."
            )
        if kind == "ai":
            return (
                "- Why it matters: AI transformation teams can convert the signal into "
                "agent governance, model evaluation, cost control, and AI safety needs."
            )
        return (
            "- Why it matters: Financial institutions can map the signal to third-party "
            "AI risk, model governance, resilience, wealth AI controls, and supervision."
        )

    def _chinese_why_it_matters(self, profile_name: str) -> str:
        kind = self._profile_kind(profile_name)
        if kind == "web3":
            return (
                "- 重要性：FinTech 与 Web3 团队可将该信号转化为储备、托管、"
                "网络安全、流动性和声誉风险监控。"
            )
        if kind == "ai":
            return (
                "- 重要性：AI 转型团队可将该信号转化为 agent 治理、模型评估、"
                "成本控制、平台依赖和 AI safety 要求。"
            )
        return (
            "- 重要性：金融机构可将该信号映射到第三方 AI 风险、模型治理、"
            "运营韧性、财富管理 AI 控制和监管准备。"
        )

    def _english_monitoring_action(self, item: dict) -> str:
        tags = set(item.get("risk_tags", []))
        if "model_risk" in tags or "ai_governance_risk" in tags:
            return (
                "- Suggested monitoring action: Track model validation evidence, "
                "evaluation results, challenger tests, drift alerts, and approvals."
            )
        if "operational_risk" in tags or "third_party_risk" in tags:
            return (
                "- Suggested monitoring action: Monitor fallback procedures, incident "
                "response readiness, vendor SLAs, attestations, and outages."
            )
        if "cybersecurity_risk" in tags:
            return (
                "- Suggested monitoring action: Watch access-control changes, fraud "
                "alerts, breach indicators, phishing reports, and privileged activity."
            )
        if "regulatory_risk" in tags:
            return (
                "- Suggested monitoring action: Track consultation papers, enforcement "
                "updates, supervisory expectations, deadlines, and policy divergences."
            )
        if "market_risk" in tags or "liquidity_risk" in tags:
            return (
                "- Suggested monitoring action: Monitor liquidity, volatility, funding, "
                "reserve stress, redemption queues, and market depth."
            )
        if "reputational_risk" in tags:
            return (
                "- Suggested monitoring action: Track complaints, customer trust, media "
                "pressure, social escalation, and remediation commitments."
            )
        return (
            "- Suggested monitoring action: Keep the signal on watch and look for "
            "corroborating primary-source evidence."
        )

    def _chinese_monitoring_action(self, item: dict) -> str:
        tags = set(item.get("risk_tags", []))
        if "model_risk" in tags or "ai_governance_risk" in tags:
            return (
                "- 建议监控动作：跟踪模型验证证据、评估结果、challenger tests、漂移告警和审批例外。"
            )
        if "operational_risk" in tags or "third_party_risk" in tags:
            return (
                "- 建议监控动作：监控 fallback procedures、事件响应准备、"
                "供应商 SLA、控制证明和中断报告。"
            )
        if "cybersecurity_risk" in tags:
            return (
                "- 建议监控动作：关注访问控制变化、欺诈监控告警、泄露指标、钓鱼报告和高权限活动。"
            )
        if "regulatory_risk" in tags:
            return "- 建议监控动作：跟踪咨询文件、执法更新、监管预期、合规期限和政策差异。"
        if "market_risk" in tags or "liquidity_risk" in tags:
            return "- 建议监控动作：监控流动性、波动率、融资条件、储备压力、赎回队列和市场深度。"
        if "reputational_risk" in tags:
            return "- 建议监控动作：跟踪投诉、客户信任指标、媒体压力、舆情升级和补救承诺。"
        return "- 建议监控动作：保持观察，并寻找可交叉验证的一手证据。"

    def _english_action(self, team: str) -> str:
        if team == "strategy":
            return (
                "- Strategy team: Prioritize high-severity and act_now themes when "
                "updating roadmaps and operating models."
            )
        if team == "risk":
            return (
                "- Risk team: Convert high-severity signals into control reviews, "
                "thresholds, and evidence requests."
            )
        return (
            "- AI transformation team: Use recurring signals to define governance, "
            "evaluation, monitoring, and incident response requirements."
        )

    def _chinese_action(self, team: str) -> str:
        if team == "strategy":
            return (
                "- 战略团队：在更新路线图和运营模式时，优先处理 high severity "
                "和 act_now urgency 的主题。"
            )
        if team == "risk":
            return "- 风险团队：将高严重性信号转化为控制审查、阈值和证据要求。"
        return "- AI 转型团队：将重复出现的信号沉淀为治理、评估、监控和事件响应要求。"
