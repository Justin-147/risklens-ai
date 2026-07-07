from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate_report(self, context: dict, language: str = "en") -> str:
        raise NotImplementedError
