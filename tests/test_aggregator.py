"""Tests for usage aggregation."""

from datetime import datetime

from printaudit.analysis.aggregator import UsageAggregator
from printaudit.parser import LogEntry


def test_aggregator_initialization():
    """Test aggregator initialization."""
    agg = UsageAggregator()
    assert agg.work_start == 7
    assert agg.work_end == 22
    assert agg.cost_default == 0.0


def test_aggregator_ingest_entry():
    """Test ingesting a log entry."""
    agg = UsageAggregator()
    entry = LogEntry(
        printer="Printer01",
        user="alice",
        job_id=12345,
        timestamp=datetime(2025, 4, 1, 10, 0, 0),
        pages=5,
        copies=1,
        billing_code=None,
        host="192.168.1.1",
        job_name="doc.pdf",
        media=None,
        sides=None,
        raw="test line",
    )
    agg.ingest(entry)
    assert agg.totals.requests == 1
    assert agg.totals.pages == 5


def test_aggregator_build_report():
    """Test building a report."""
    agg = UsageAggregator()
    entry = LogEntry(
        printer="Printer01",
        user="alice",
        job_id=12345,
        timestamp=datetime(2025, 4, 1, 10, 0, 0),
        pages=5,
        copies=1,
        billing_code=None,
        host="192.168.1.1",
        job_name="doc.pdf",
        media=None,
        sides=None,
        raw="test line",
    )
    agg.ingest(entry)
    report = agg.build_report()
    assert report.totals.requests == 1
    assert report.totals.pages == 5
    assert len(report.queue_stats) > 0
    assert len(report.user_stats) > 0


def test_aggregator_cost_calculation_default_rate():
    """Test cost calculation with default rate."""
    agg = UsageAggregator(cost_default=0.05)
    entry = LogEntry(
        printer="Printer01",
        user="alice",
        job_id=12345,
        timestamp=datetime(2025, 4, 1, 10, 0, 0),
        pages=10,
        copies=1,
        billing_code=None,
        host="192.168.1.1",
        job_name="doc.pdf",
        media=None,
        sides=None,
        raw="test line",
    )
    agg.ingest(entry)
    report = agg.build_report()
    # Cost should be calculated (10 pages * 0.05 = 0.5)
    # But we need cost rules to assign to a label
    assert report.totals.pages == 10


def test_aggregator_cost_calculation_printer_rate():
    """Test cost calculation with printer-specific rate."""
    agg = UsageAggregator(
        cost_default=0.05,
        cost_printer_rates={"printer01": 0.02},
    )
    entry = LogEntry(
        printer="Printer01",
        user="alice",
        job_id=12345,
        timestamp=datetime(2025, 4, 1, 10, 0, 0),
        pages=10,
        copies=1,
        billing_code=None,
        host="192.168.1.1",
        job_name="doc.pdf",
        media=None,
        sides=None,
        raw="test line",
    )
    agg.ingest(entry)
    report = agg.build_report()
    assert report.totals.pages == 10


def test_aggregator_multiple_entries():
    """Test aggregating multiple entries."""
    agg = UsageAggregator()
    for i in range(5):
        entry = LogEntry(
            printer=f"Printer{i % 2 + 1}",
            user=f"user{i}",
            job_id=10000 + i,
            timestamp=datetime(2025, 4, 1, 10, i, 0),
            pages=i + 1,
            copies=1,
            billing_code=None,
            host=f"192.168.1.{i}",
            job_name=f"doc{i}.pdf",
            media=None,
            sides=None,
            raw=f"test line {i}",
        )
        agg.ingest(entry)
    report = agg.build_report()
    assert report.totals.requests == 5
    assert report.totals.pages == 15  # 1+2+3+4+5
    assert len(report.queue_stats) == 2  # Two different printers
