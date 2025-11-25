"""Base classes for PrintAudit outputs."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..analysis import AnalysisReport
from ..config import Config


@dataclass
class OutputContext:
    config: Config
    attachments: list[str] = field(default_factory=list)
    stdout: object | None = None

    def __post_init__(self) -> None:
        if self.stdout is None:
            self.stdout = sys.stdout


class OutputModule(ABC):
    name: str

    def __init__(self, context: OutputContext):
        self.context = context

    @abstractmethod
    def render(self, report: AnalysisReport) -> None:
        """Render output for the provided report."""


REGISTRY: dict[str, type[OutputModule]] = {}


def register_output(name: str):
    def decorator(cls: type[OutputModule]) -> type[OutputModule]:
        REGISTRY[name] = cls
        cls.name = name
        return cls

    return decorator


def get_output_module(name: str) -> type[OutputModule]:
    if name not in REGISTRY:
        raise KeyError(
            f"Unknown output module '{name}'. Available: {', '.join(REGISTRY)}"
        )
    return REGISTRY[name]


def list_outputs() -> list[str]:
    return sorted(REGISTRY.keys())
