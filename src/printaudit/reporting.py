"""High-level orchestration for PrintAudit."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from pathlib import Path

from .analysis import UsageAggregator
from .config import Config
from .outputs import OutputContext, get_output_module
from .parser import parse_page_log


def run_report(
    config: Config,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[str]:
    """Run analysis pipeline and return generated artifact paths."""

    aggregator = UsageAggregator(
        cost_rules=config.cost_inference_rules,
        work_start=config.work_start,
        work_end=config.work_end,
    )
    page_log = Path(config.page_log_path)

    for entry in parse_page_log(page_log):
        entry_date = entry.timestamp.date()
        if start_date and entry_date < start_date:
            continue
        if end_date and entry_date > end_date:
            continue
        aggregator.ingest(entry)

    report = aggregator.build_report()
    context = OutputContext(config=config)

    outputs = _ordered_outputs(config.outputs)
    for name in outputs:
        module_cls = get_output_module(name)
        module = module_cls(context)
        module.render(report)

    return context.attachments


def _ordered_outputs(outputs: Iterable[str]) -> list[str]:
    # Ensure email runs last if present
    sanitized = [name.strip().lower() for name in outputs if name.strip()]
    if "email" in sanitized:
        sanitized = [name for name in sanitized if name != "email"] + ["email"]
    return sanitized
