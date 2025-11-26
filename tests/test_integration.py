"""Integration tests for PrintAudit workflow."""

from printaudit.analysis.aggregator import UsageAggregator
from printaudit.config import parse_config
from printaudit.parser import parse_page_log


def test_end_to_end_workflow(tmp_path):
    """Test complete workflow from log file to report."""
    # Create test log file
    log_file = tmp_path / "page_log"
    log_file.write_text(
        "Printer01 alice 12345 [01/Apr/2025:09:03:11 -0300] "
        "total 5 - 192.168.1.1 doc.pdf - -\n"
        "Printer02 bob 12346 [01/Apr/2025:10:00:00 -0300] "
        "total 10 - 192.168.1.2 report.pdf - -\n"
        "Printer01 alice 12347 [01/Apr/2025:11:00:00 -0300] "
        "total 3 - 192.168.1.1 invoice.pdf - -\n"
    )

    # Create test config
    config_file = tmp_path / "printaudit.conf"
    config_file.write_text(
        f"""[core]
page_log_path={log_file}
work_start=7
work_end=22
outputs=cli
"""
    )

    # Parse config
    config = parse_config(config_file)

    # Parse log entries
    entries = list(parse_page_log(config.page_log_path))

    # Aggregate data
    agg = UsageAggregator(
        work_start=config.work_start,
        work_end=config.work_end,
    )

    for entry in entries:
        agg.ingest(entry)

    # Build report
    report = agg.build_report()

    # Verify results
    assert report.totals.requests == 3
    assert report.totals.pages == 18  # 5 + 10 + 3
    assert len(report.queue_stats) == 2  # Two printers
    assert len(report.user_stats) == 2  # Two users
    # Queue stats are sorted by pages (descending)
    queue_names = [stat.queue for stat in report.queue_stats]
    assert "Printer01" in queue_names
    assert "Printer02" in queue_names
    # Printer02 has more pages (10) so should be first
    assert report.queue_stats[0].queue == "Printer02"
    assert report.queue_stats[0].pages == 10
