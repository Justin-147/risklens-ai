from __future__ import annotations

import os

from risklens.llm.mock_provider import MockLLMProvider
from risklens.llm.provider import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL") or None
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    def generate_report(self, context: dict, language: str = "en") -> str:
        fallback = MockLLMProvider().generate_report(context, language=language)
        language_instruction = (
            "Write the report in Simplified Chinese."
            if language == "zh"
            else "Write the report in English."
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You create risk-aware intelligence briefs from supplied JSON evidence."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{language_instruction}\nEvidence JSON:\n{context}\n\n"
                        f"Draft format to preserve:\n{fallback}"
                    ),
                },
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or fallback
