"""Email dispatcher output module."""

from __future__ import annotations

from pathlib import Path

from ..analysis import AnalysisReport
from ..emailer import EmailClient, EmailDeliveryError
from .base import OutputModule, register_output


@register_output("email")
class EmailOutput(OutputModule):
    def render(self, report: AnalysisReport) -> None:
        settings = self.context.config.email
        if not settings.enabled:
            return

        client = EmailClient(settings)
        attachments = self._select_attachments()
        subject = settings.subject or "PrintAudit Report"
        totals = report.totals
        start_date = totals.first_event.date()
        end_date = totals.last_event.date()
        body = (
            "PrintAudit summary\n"
            f"Requests: {totals.requests}\n"
            f"Pages: {totals.pages}\n"
            f"Window: {start_date} -> {end_date}\n"
        )
        try:
            client.send_report(subject, body, attachments)
        except EmailDeliveryError as exc:  # pragma: no cover - network heavy
            print(f"[printaudit] email delivery failed: {exc}")

    def _select_attachments(self) -> list[Path]:
        paths = [Path(p) for p in self.context.attachments]
        settings = self.context.config.email
        selected: list[Path] = []
        for path in paths:
            if path.suffix == ".csv" and settings.attach_csv:
                selected.append(path)
            if path.suffix in {".htm", ".html"} and settings.attach_html:
                selected.append(path)
        return selected
