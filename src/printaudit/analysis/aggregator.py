"""Core data aggregation for PrintAudit."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import DefaultDict

from .. import parser


@dataclass
class Totals:
    requests: int = 0
    pages: int = 0
    first_event: datetime | None = None
    last_event: datetime | None = None


@dataclass
class QueueStat:
    queue: str
    requests_pct: float
    pages_pct: float
    requests: int
    pages: int


@dataclass
class QueueUserStat:
    queue: str
    user: str
    pages: int


@dataclass
class UserStat:
    user: str
    requests: int
    pages: int
    pages_per_request: float


@dataclass
class TemporalPoint:
    key: str  # hour (00-23) or date (YYYY-MM-DD)
    requests: int
    pages: int
    within_hours: bool | None = None


@dataclass
class JobBucket:
    label: str
    pct_requests: float
    request_count: int


@dataclass
class CopyBucket:
    label: str
    pct_requests: float
    request_count: int


@dataclass
class CostStat:
    label: str
    pages: int
    per_user: list[tuple[str, int]] = field(default_factory=list)
    per_queue: list[tuple[str, int]] = field(default_factory=list)
    amount: float = 0.0


@dataclass
class SimpleStat:
    label: str
    pages: int


@dataclass
class AnalysisReport:
    totals: Totals
    queue_stats: list[QueueStat]
    queue_user_stats: list[QueueUserStat]
    user_stats: list[UserStat]
    hourly: list[TemporalPoint]
    daily: list[TemporalPoint]
    job_buckets: list[JobBucket]
    copy_buckets: list[CopyBucket]
    cost_stats: list[CostStat]
    client_stats: list[SimpleStat]
    document_types: list[SimpleStat]
    media_stats: list[SimpleStat]
    duplex_stats: list[SimpleStat]


JOB_BUCKETS = [
    (0, 10, "0-10"),
    (11, 20, "11-20"),
    (21, 30, "21-30"),
    (31, 40, "31-40"),
    (41, 50, "41-50"),
    (51, 100, "51-100"),
    (101, 200, "101-200"),
    (201, None, "200+"),
]

COPY_BUCKETS = [
    (1, 1, "1"),
    (2, 2, "2"),
    (3, 3, "3"),
    (4, 4, "4"),
    (5, 10, "5-10"),
    (11, 20, "11-20"),
    (21, 30, "21-30"),
    (31, 40, "31-40"),
    (41, 50, "41-50"),
    (51, 100, "51-100"),
    (101, None, "100+"),
]


class UsageAggregator:
    """Incrementally compute PrintAudit statistics."""

    def __init__(
        self,
        cost_rules: dict[str, str] | None = None,
        work_start: int = 7,
        work_end: int = 22,
        cost_default: float = 0.0,
        cost_printer_rates: dict[str, float] | None = None,
        cost_label_rates: dict[str, float] | None = None,
    ):
        self.totals = Totals()
        self.queue_requests: Counter[str] = Counter()
        self.queue_pages: Counter[str] = Counter()
        self.queue_user_pages: Counter[tuple[str, str]] = Counter()
        self.user_requests: Counter[str] = Counter()
        self.user_pages: Counter[str] = Counter()
        self.hourly: Counter[str] = Counter()
        self.hourly_pages: Counter[str] = Counter()
        self.daily: Counter[str] = Counter()
        self.daily_pages: Counter[str] = Counter()
        self.job_histogram: Counter[str] = Counter()
        self.copy_histogram: Counter[str] = Counter()
        self.cost_pages: Counter[str] = Counter()
        self.cost_user_pages: DefaultDict[str, Counter[str]] = defaultdict(
            Counter
        )
        self.cost_queue_pages: DefaultDict[str, Counter[str]] = defaultdict(
            Counter
        )
        self.client_pages: Counter[str] = Counter()
        self.document_pages: Counter[str] = Counter()
        self.media_pages: Counter[str] = Counter()
        self.duplex_pages: Counter[str] = Counter()
        self.cost_rules = cost_rules or {}
        self.work_start = work_start
        self.work_end = work_end
        self.cost_default = cost_default
        self.cost_printer_rates = cost_printer_rates or {}
        self.cost_label_rates = cost_label_rates or {}

    def ingest(self, entry: parser.LogEntry) -> None:
        self.totals.requests += 1
        self.totals.pages += entry.pages
        if (
            not self.totals.first_event
            or entry.timestamp < self.totals.first_event
        ):
            self.totals.first_event = entry.timestamp
        if (
            not self.totals.last_event
            or entry.timestamp > self.totals.last_event
        ):
            self.totals.last_event = entry.timestamp

        # Queue stats
        self.queue_requests[entry.printer] += 1
        self.queue_pages[entry.printer] += entry.pages
        self.queue_user_pages[(entry.printer, entry.user)] += entry.pages

        # User stats
        self.user_requests[entry.user] += 1
        self.user_pages[entry.user] += entry.pages

        # Temporal
        hour_key = entry.timestamp.strftime("%H:00")
        day_key = entry.timestamp.strftime("%Y-%m-%d")
        self.hourly[hour_key] += 1
        self.hourly_pages[hour_key] += entry.pages
        self.daily[day_key] += 1
        self.daily_pages[day_key] += entry.pages

        # Job / copy buckets
        self.job_histogram[self._bucketize(entry.pages, JOB_BUCKETS)] += 1
        self.copy_histogram[self._bucketize(entry.copies, COPY_BUCKETS)] += 1

        # Cost analysis
        billing = entry.billing_code or self._infer_billing(entry)
        label = billing or "unassigned"
        self.cost_pages[label] += entry.pages
        self.cost_user_pages[label][entry.user] += entry.pages
        self.cost_queue_pages[label][entry.printer] += entry.pages

        # Client analysis
        client_label = entry.host or "unknown"
        self.client_pages[client_label] += entry.pages

        # Document types
        doc_type = _document_extension(entry.job_name)
        self.document_pages[doc_type] += entry.pages

        # Media / duplex
        media_label = entry.media or "unknown"
        self.media_pages[media_label] += entry.pages
        duplex_label = normalize_duplex(entry.sides)
        self.duplex_pages[duplex_label] += entry.pages

    def build_report(self) -> AnalysisReport:
        totals = self.totals
        queue_stats = self._build_queue_stats()
        queue_user_stats = sorted(
            (
                QueueUserStat(queue=q, user=u, pages=pages)
                for (q, u), pages in self.queue_user_pages.items()
            ),
            key=lambda item: (-item.pages, item.queue, item.user),
        )
        user_stats = self._build_user_stats()
        hourly = []
        for h in sorted(self.hourly.keys()):
            hour_int = int(h.split(":", 1)[0])
            within = self.work_start <= hour_int <= self.work_end
            hourly.append(
                TemporalPoint(
                    key=h,
                    requests=self.hourly[h],
                    pages=self.hourly_pages[h],
                    within_hours=within,
                )
            )
        daily = [
            TemporalPoint(
                key=d,
                requests=self.daily[d],
                pages=self.daily_pages[d],
                within_hours=None,
            )
            for d in sorted(self.daily.keys())
        ]
        job_buckets = self._build_bucket_section(self.job_histogram)
        copy_buckets = self._build_bucket_section(self.copy_histogram)
        cost_stats = self._build_cost_stats()
        client_stats = self._simple_stats(self.client_pages)
        document_types = self._simple_stats(self.document_pages)
        media_stats = self._simple_stats(self.media_pages)
        duplex_stats = self._simple_stats(self.duplex_pages)

        return AnalysisReport(
            totals=totals,
            queue_stats=queue_stats,
            queue_user_stats=queue_user_stats,
            user_stats=user_stats,
            hourly=hourly,
            daily=daily,
            job_buckets=job_buckets,
            copy_buckets=copy_buckets,
            cost_stats=cost_stats,
            client_stats=client_stats,
            document_types=document_types,
            media_stats=media_stats,
            duplex_stats=duplex_stats,
        )

    def _build_queue_stats(self) -> list[QueueStat]:
        total_requests = max(self.totals.requests, 1)
        total_pages = max(self.totals.pages, 1)
        stats = []
        for queue, pages in self.queue_pages.most_common():
            requests = self.queue_requests[queue]
            stats.append(
                QueueStat(
                    queue=queue,
                    requests_pct=round(100 * requests / total_requests, 2),
                    pages_pct=round(100 * pages / total_pages, 2),
                    requests=requests,
                    pages=pages,
                )
            )
        return stats

    def _build_user_stats(self) -> list[UserStat]:
        stats = []
        for user, pages in self.user_pages.most_common():
            requests = self.user_requests[user]
            ratio = pages / requests if requests else 0
            stats.append(
                UserStat(
                    user=user,
                    requests=requests,
                    pages=pages,
                    pages_per_request=round(ratio, 2),
                )
            )
        return stats

    def _build_bucket_section(
        self, histogram: Counter[str]
    ) -> list[JobBucket]:
        if not histogram:
            return []
        total = sum(histogram.values())
        result = []
        for label, count in histogram.items():
            pct = round(100 * count / total, 2)
            result.append(
                JobBucket(
                    label=label,
                    pct_requests=pct,
                    request_count=count,
                )
            )
        return sorted(result, key=lambda b: b.label)

    def _build_cost_stats(self) -> list[CostStat]:
        stats = []
        for label, pages in self.cost_pages.most_common():
            amount = 0.0
            if (
                self.cost_default
                or self.cost_printer_rates
                or self.cost_label_rates
            ):
                queue_pages = self.cost_queue_pages[label]
                for queue, q_pages in queue_pages.items():
                    rate = self._resolve_rate(label, queue)
                    amount += q_pages * rate
            stats.append(
                CostStat(
                    label=label,
                    pages=pages,
                    per_user=_top_items(self.cost_user_pages[label]),
                    per_queue=_top_items(self.cost_queue_pages[label]),
                    amount=amount,
                )
            )
        return stats

    def _resolve_rate(self, label: str, queue: str) -> float:
        """Determine effective rate for a given cost label and queue."""

        label_key = label.lower()
        queue_key = queue.lower()
        if label_key in self.cost_label_rates:
            return self.cost_label_rates[label_key]
        if queue_key in self.cost_printer_rates:
            return self.cost_printer_rates[queue_key]
        return self.cost_default

    def _simple_stats(self, counter: Counter[str]) -> list[SimpleStat]:
        return [
            SimpleStat(label=label, pages=pages)
            for label, pages in counter.most_common()
        ]

    def _infer_billing(self, entry: parser.LogEntry) -> str | None:
        if not self.cost_rules:
            return None
        haystack = " ".join(
            filter(
                None,
                [
                    entry.printer,
                    entry.user,
                    entry.job_name or "",
                    entry.host or "",
                ],
            )
        ).lower()
        for label, raw_tokens in self.cost_rules.items():
            tokens = [
                token.strip().lower()
                for token in re_splitter(raw_tokens)
                if token.strip()
            ]
            if not tokens:
                continue
            if any(token in haystack for token in tokens):
                return label
        return None

    @staticmethod
    def _bucketize(
        value: int, buckets: Sequence[tuple[int | None, int | None, str]]
    ) -> str:
        for low, high, label in buckets:
            if low is not None and value < low:
                continue
            if high is not None and value > high:
                continue
            return label
        return f">{buckets[-1][1]}" if buckets and buckets[-1][1] else "other"


def _document_extension(name: str | None) -> str:
    if not name or name == "unknown":
        return "unknown"
    lowered = name.lower()
    if "." not in lowered:
        return "unknown"
    ext = lowered.rsplit(".", 1)[-1]
    if ext not in COMMON_EXTENSIONS:
        return "unknown"
    return ext


COMMON_EXTENSIONS = {
    # Documents
    "pdf",
    "doc",
    "docx",
    "odt",
    "rtf",
    "txt",
    "pages",
    # Spreadsheets
    "xls",
    "xlsx",
    "xlsm",
    "csv",
    "ods",
    "numbers",
    # Presentations
    "ppt",
    "pptx",
    "odp",
    "key",
    # Images
    "jpg",
    "jpeg",
    "png",
    "gif",
    "bmp",
    "tiff",
    "tif",
    "svg",
    # Reports
    "frx",
    "rpt",
    "mrt",
    "rep",
    # Web/Data
    "html",
    "htm",
    "xml",
    "json",
    "log",
    # Print Formats
    "ps",
    "eps",
    "prn",
    # Development
    "cgi",
    "md",
    "tex",
}


def normalize_duplex(sides: str | None) -> str:
    if not sides:
        return "unknown"
    value = sides.lower()
    if value.startswith("two-sided"):
        return "duplex"
    if value in {"one-sided", "simplex"}:
        return "simplex"
    return value


def _top_items(counter: Counter[str], limit: int = 5) -> list[tuple[str, int]]:
    return counter.most_common(limit)


def re_splitter(raw: str) -> list[str]:
    delimiters = [",", "|", ";"]
    tokens = [raw]
    for delim in delimiters:
        tokens = [
            subtoken for token in tokens for subtoken in token.split(delim)
        ]
    return tokens
