"""CSV export module."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from pathlib import Path

from ..analysis import AnalysisReport
from .base import OutputModule, register_output


@register_output("csv")
class CsvOutput(OutputModule):
    def render(self, report: AnalysisReport) -> None:
        target = Path(self.context.config.csv_dir)
        target.mkdir(parents=True, exist_ok=True)

        writers = [
            (
                "queue",
                ["queue", "requests_pct", "pages_pct", "requests", "pages"],
                (
                    [
                        stat.queue,
                        stat.requests_pct,
                        stat.pages_pct,
                        stat.requests,
                        stat.pages,
                    ]
                    for stat in report.queue_stats
                ),
            ),
            (
                "queue_user",
                ["queue", "user", "pages"],
                (
                    [stat.queue, stat.user, stat.pages]
                    for stat in report.queue_user_stats
                ),
            ),
            (
                "users",
                ["user", "requests", "pages", "pages_per_request"],
                (
                    [
                        stat.user,
                        stat.requests,
                        stat.pages,
                        stat.pages_per_request,
                    ]
                    for stat in report.user_stats
                ),
            ),
            (
                "hourly",
                ["hour", "requests", "pages"],
                (
                    [
                        point.key,
                        point.requests,
                        point.pages,
                    ]
                    for point in report.hourly
                ),
            ),
            (
                "daily",
                ["date", "requests", "pages"],
                (
                    [
                        point.key,
                        point.requests,
                        point.pages,
                    ]
                    for point in report.daily
                ),
            ),
            (
                "job_buckets",
                ["bucket", "pct_requests", "requests"],
                (
                    [bucket.label, bucket.pct_requests, bucket.request_count]
                    for bucket in report.job_buckets
                ),
            ),
            (
                "copy_buckets",
                ["bucket", "pct_requests", "requests"],
                (
                    [bucket.label, bucket.pct_requests, bucket.request_count]
                    for bucket in report.copy_buckets
                ),
            ),
            (
                "cost",
                ["label", "pages", "top_users", "top_queues"],
                (
                    [
                        stat.label,
                        stat.pages,
                        ";".join(f"{u}:{p}" for u, p in stat.per_user),
                        ";".join(f"{q}:{p}" for q, p in stat.per_queue),
                    ]
                    for stat in report.cost_stats
                ),
            ),
            (
                "clients",
                ["client", "pages"],
                ([stat.label, stat.pages] for stat in report.client_stats),
            ),
            (
                "document_types",
                ["extension", "pages"],
                ([stat.label, stat.pages] for stat in report.document_types),
            ),
            (
                "media",
                ["media", "pages"],
                ([stat.label, stat.pages] for stat in report.media_stats),
            ),
            (
                "duplex",
                ["mode", "pages"],
                ([stat.label, stat.pages] for stat in report.duplex_stats),
            ),
        ]

        for name, headers, rows in writers:
            self._write_csv(target / f"{name}.csv", headers, rows)

    def _write_csv(
        self,
        path: Path,
        headers: Sequence[str],
        rows: Iterable[Sequence],
    ) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)
        self.context.attachments.append(str(path))
