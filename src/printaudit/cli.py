"""Command-line entry point for PrintAudit."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path

from . import config
from .outputs import list_outputs
from .reporting import run_report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="printaudit",
        description="PrintAudit - Analyze CUPS page_log usage statistics.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help=(
            "Path to printaudit.conf "
            "(defaults to /etc/printaudit/printaudit.conf)."
        ),
    )
    parser.add_argument(
        "-o",
        "--outputs",
        help=(
            "Comma-separated override for output modules "
            "(e.g., cli,csv,html)."
        ),
    )
    parser.add_argument(
        "--cli-mode",
        choices=["plain", "rich"],
        help="Override CLI renderer style.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse config and show summary without running analyses.",
    )
    parser.add_argument(
        "--list-outputs",
        action="store_true",
        help="List available output modules and exit.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Only include entries on/after YYYY-MM-DD.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="Only include entries on/before YYYY-MM-DD.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.list_outputs:
        print("Available outputs: " + ", ".join(list_outputs()))
        return 0

    try:
        loaded = config.parse_config(args.config)
    except config.ConfigError as exc:
        parser.error(str(exc))
        return 2

    if args.outputs:
        loaded.outputs = [
            item.strip() for item in args.outputs.split(",") if item.strip()
        ]
    if args.cli_mode:
        loaded.cli_mode = args.cli_mode

    if args.dry_run:
        print("PrintAudit configuration:")
        print(f"  page_log_path: {loaded.page_log_path}")
        print(
            f"  work hours   : "
            f"{loaded.work_start:02d}-{loaded.work_end:02d}"
        )
        print(f"  outputs      : {', '.join(loaded.outputs)}")
        print(f"  cli_mode     : {loaded.cli_mode}")
        print(f"  csv_dir      : {loaded.csv_dir}")
        print(f"  html_path    : {loaded.html_path}")
        if loaded.email.enabled:
            print(
                "  email        : enabled -> "
                f"{loaded.email.smtp_host}:{loaded.email.smtp_port} "
                f"recipients={','.join(loaded.email.recipients)}"
            )
        else:
            print("  email        : disabled")
        return 0

    start_date = _parse_date(args.start_date) if args.start_date else None
    end_date = _parse_date(args.end_date) if args.end_date else None

    attachments = run_report(loaded, start_date=start_date, end_date=end_date)
    if attachments:
        print("Artifacts generated:")
        for path in attachments:
            print(f"  {path}")
    return 0


def _parse_date(raw: str) -> date:
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:  # pragma: no cover - argument parsing
        raise SystemExit(f"Invalid date '{raw}'. Use YYYY-MM-DD.") from exc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
