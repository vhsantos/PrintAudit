"""Utilities to read and normalize CUPS page_log entries."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

LOGGER = logging.getLogger(__name__)
DATE_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


LINE_HEADER = re.compile(
    r"""
    ^
    (?P<printer>\S+)\s+
    (?P<user>\S+)\s+
    (?P<job_id>\d+)\s+
    \[(?P<timestamp>[^\]]+)\]\s+
    (?P<rest>.+)
    $
    """,
    re.VERBOSE,
)


@dataclass
class LogEntry:
    printer: str
    user: str
    job_id: int
    timestamp: datetime
    pages: int
    copies: int
    billing_code: str | None
    host: str | None
    job_name: str | None
    media: str | None
    sides: str | None
    raw: str


def parse_page_log(path: Path) -> Iterator[LogEntry]:
    """Yield normalized :class:`LogEntry` rows from a page_log file."""

    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                entry = parse_line(line)
            except ValueError as exc:
                LOGGER.warning("Skipping line %d: %s", line_number, exc)
                continue
            yield entry


def parse_line(line: str) -> LogEntry:
    """Parse a single page_log line."""

    match = LINE_HEADER.match(line)
    if not match:
        raise ValueError("unrecognized header")

    printer = match.group("printer")
    user = normalize_user(match.group("user"))
    job_id = int(match.group("job_id"))
    timestamp = datetime.strptime(match.group("timestamp"), DATE_FORMAT)
    rest = match.group("rest")

    (
        pages,
        copies,
        billing_code,
        host,
        job_name,
        media,
        sides,
    ) = _parse_rest(rest)

    return LogEntry(
        printer=printer,
        user=user,
        job_id=job_id,
        timestamp=timestamp,
        pages=pages,
        copies=copies,
        billing_code=billing_code,
        host=host,
        job_name=job_name,
        media=media,
        sides=sides,
        raw=line,
    )


def _parse_rest(
    rest: str,
) -> tuple[
    int, int, str | None, str | None, str | None, str | None, str | None
]:
    """
    Parse the remainder of a page_log row.

    Supports both legacy PrintAnalyzer format
    (pages copies billing) and default CUPS format
    (total pages billing host jobname media sides).
    """

    if not rest:
        raise ValueError("missing data payload")

    tokens = rest.split()
    if not tokens:
        raise ValueError("missing tokens in payload")

    if tokens[0].isdigit():
        # Legacy format: pages copies billing
        if len(tokens) < 3:
            raise ValueError("legacy payload too short")
        pages = int(tokens[0])
        copies = int(tokens[1])
        billing = normalize_billing(tokens[2])
        return pages, copies, billing, None, None, None, None

    # Default CUPS format
    keyword = tokens[0].lower()
    if keyword not in {"total", "page"}:
        raise ValueError(f"unknown keyword '{tokens[0]}'")
    if len(tokens) < 4:
        raise ValueError("default payload too short")

    pages = int(tokens[1])
    copies = 1  # default format omits explicit copies
    billing = normalize_billing(tokens[2])
    remaining = tokens[3:]

    if len(remaining) < 3:
        raise ValueError("default payload missing host/job/media info")

    host = normalize_optional(remaining[0])
    media = normalize_optional(remaining[-2])
    sides = normalize_optional(remaining[-1])
    job_name_tokens = remaining[1:-2]
    job_name = None
    if job_name_tokens:
        job_name = normalize_optional(" ".join(job_name_tokens))

    return pages, copies, billing, host, job_name, media, sides


def normalize_user(user: str) -> str:
    result = user.strip().lower()
    return result or "unknown"


def normalize_billing(value: str) -> str | None:
    normalized = normalize_optional(value)
    if normalized in {None, "-none-"}:
        return None
    return normalized


def normalize_optional(value: str) -> str | None:
    stripped = value.strip()
    if stripped in {"", "-"}:
        return None
    return stripped
