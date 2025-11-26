"""CLI output formats."""

from __future__ import annotations

from textwrap import indent

from ..analysis import AnalysisReport
from ..analysis.aggregator import TemporalPoint
from .base import OutputModule, register_output


@register_output("cli")
class CliOutput(OutputModule):
    """Plain or rich CLI report."""

    def render(self, report: AnalysisReport) -> None:
        mode = (self.context.config.cli_mode or "plain").lower()
        if mode == "rich":
            self._render_rich(report)
        else:
            self._render_plain(report)

    def _render_plain(self, report: AnalysisReport) -> None:
        out = self.context.stdout
        totals = report.totals
        print("EXECUTIVE SUMMARY", file=out)
        print(
            f"Requests: {totals.requests} | Pages: {totals.pages} | "
            f"Window: {totals.first_event} -> {totals.last_event}",
            file=out,
        )
        print("", file=out)
        self._print_queue_section(report, out, rich=False)
        self._print_user_section(report, out, rich=False)
        self._print_temporal_section(report, out, rich=False)
        self._print_job_section(report, out, rich=False)
        self._print_cost_section(report, out, rich=False)
        self._print_media_section(report, out, rich=False)

    def _render_rich(self, report: AnalysisReport) -> None:
        out = self.context.stdout
        totals = report.totals
        print("=" * 72, file=out)
        summary = (
            f"PrintAudit Summary ({totals.first_event} -> "
            f"{totals.last_event})"
        )
        print(summary, file=out)
        requests = totals.requests
        pages = totals.pages
        totals_line = (
            f"Total Requests: {requests:>6} | Total Pages: {pages:>6}"
        )
        print(totals_line, file=out)
        print("=" * 72, file=out)
        self._print_queue_section(report, out, rich=True)
        self._print_user_section(report, out, rich=True)
        self._print_temporal_section(report, out, rich=True)
        self._print_job_section(report, out, rich=True)
        self._print_cost_section(report, out, rich=True)
        self._print_media_section(report, out, rich=True)

    def _print_queue_section(
        self, report: AnalysisReport, out, rich: bool
    ) -> None:
        print("QUEUE ANALYSIS", file=out)
        rows = [
            [
                stat.queue,
                f"{stat.requests_pct:5.1f}%",
                f"{stat.pages_pct:5.1f}%",
                stat.requests,
                stat.pages,
            ]
            for stat in report.queue_stats
        ]
        self._emit_table(
            out,
            ["Queue", "%Req", "%Pages", "Req", "Pages"],
            rows,
            rich,
        )
        if report.queue_user_stats:
            print("Queue-User breakdown:", file=out)
            for item in report.queue_user_stats[:10]:
                line = (
                    f"{item.queue:<20} {item.user:<20} "
                    f"{item.pages:>6} pages"
                )
                print(indent(line, "  "), file=out)
        print("", file=out)

    def _print_user_section(
        self, report: AnalysisReport, out, rich: bool
    ) -> None:
        max_rows = self.context.config.cli_max_rows
        print("USER ANALYSIS", file=out)
        rows = [
            [
                stat.user,
                stat.requests,
                stat.pages,
                f"{stat.pages_per_request:5.2f}",
            ]
            for stat in report.user_stats
        ]
        self._emit_table(
            out,
            ["User", "Req", "Pages", "Pages/Req"],
            rows,
            rich,
            limit=max_rows,
        )
        print("", file=out)

    def _print_temporal_section(
        self, report: AnalysisReport, out, rich: bool
    ) -> None:
        print("TEMPORAL ANALYSIS", file=out)
        print("Hour usage:", file=out)
        self._emit_temporal(out, report.hourly, rich)
        print("Daily usage:", file=out)
        self._emit_temporal(out, report.daily, rich)
        print("", file=out)

    def _print_job_section(
        self, report: AnalysisReport, out, rich: bool
    ) -> None:
        print("JOB ANALYSIS", file=out)
        job_rows = [
            [
                bucket.label,
                f"{bucket.pct_requests:5.1f}%",
                bucket.request_count,
            ]
            for bucket in report.job_buckets
        ]
        self._emit_table(out, ["Job Size", "%Req", "Requests"], job_rows, rich)
        copy_rows = [
            [
                bucket.label,
                f"{bucket.pct_requests:5.1f}%",
                bucket.request_count,
            ]
            for bucket in report.copy_buckets
        ]
        print("Copies:", file=out)
        self._emit_table(out, ["Copies", "%Req", "Requests"], copy_rows, rich)
        print("", file=out)

    def _print_cost_section(
        self, report: AnalysisReport, out, rich: bool
    ) -> None:
        print("COST ANALYSIS", file=out)
        rows = [
            [
                stat.label,
                stat.pages,
                self._format_currency(stat.amount),
                ", ".join(f"{u}:{p}" for u, p in stat.per_user),
            ]
            for stat in report.cost_stats
        ]
        self._emit_table(
            out, ["Label", "Pages", "Cost", "Top Users"], rows, rich
        )
        print("", file=out)

    def _format_currency(self, amount: float) -> str:
        config = self.context.config
        symbol = getattr(config, "currency_symbol", "")
        code = getattr(config, "currency_code", "")
        if symbol:
            return f"{symbol}{amount:,.0f}"
        if code:
            return f"{amount:,.0f} {code}"
        return f"{amount:,.2f}"

    def _print_media_section(
        self, report: AnalysisReport, out, rich: bool
    ) -> None:
        print("MEDIA & CLIENT ANALYSIS", file=out)
        media_rows = [[stat.label, stat.pages] for stat in report.media_stats]
        self._emit_table(out, ["Media", "Pages"], media_rows, rich)
        client_rows = [
            [stat.label, stat.pages] for stat in report.client_stats
        ]
        print("Top clients:", file=out)
        self._emit_table(
            out,
            ["Client", "Pages"],
            client_rows,
            rich,
            limit=self.context.config.cli_max_rows,
        )
        doc_rows = [[stat.label, stat.pages] for stat in report.document_types]
        print("Document types:", file=out)
        self._emit_table(out, ["Extension", "Pages"], doc_rows, rich)
        duplex_rows = [
            [stat.label, stat.pages] for stat in report.duplex_stats
        ]
        print("Duplex:", file=out)
        self._emit_table(out, ["Mode", "Pages"], duplex_rows, rich)
        print("", file=out)

    def _emit_table(
        self, out, headers, rows, rich: bool, limit: int | None = None
    ) -> None:
        if not rows:
            print("  (no data)", file=out)
            return
        display_rows = rows if limit is None else rows[:limit]
        if not rich:
            for row in display_rows:
                line = "  " + " | ".join(str(cell) for cell in row)
                print(line, file=out)
            if limit is not None and len(rows) > limit:
                print(f"  ... ({len(rows)} rows)", file=out)
            return

        widths = [len(header) for header in headers]
        for row in display_rows:
            for idx, cell in enumerate(row):
                widths[idx] = max(widths[idx], len(str(cell)))

        def fmt_row(row):
            return " | ".join(
                str(cell).ljust(widths[idx]) for idx, cell in enumerate(row)
            )

        bar = "-+-".join("-" * width for width in widths)
        print("  " + fmt_row(headers), file=out)
        print("  " + bar, file=out)
        for row in display_rows:
            print("  " + fmt_row(row), file=out)
        if limit is not None and len(rows) > limit:
            print(f"  ... ({len(rows)} rows)", file=out)

    def _emit_temporal(
        self, out, data: list[TemporalPoint], rich: bool
    ) -> None:
        if not data:
            print("  (no data)", file=out)
            return
        if not rich:
            for point in data[:24]:
                marker = "" if point.within_hours in {None, True} else " !"
                msg = (
                    f"  {point.key}: {point.requests} req / "
                    f"{point.pages} pages{marker}"
                )
                print(msg, file=out)
            return
        headers = ["Key", "Requests", "Pages"]
        rows = []
        for point in data:
            if point.within_hours is None:
                flag = ""
            else:
                flag = "in-hours" if point.within_hours else "off-hours"
            rows.append([point.key, point.requests, point.pages, flag])
        self._emit_table(out, headers + ["Flag"], rows, True)
