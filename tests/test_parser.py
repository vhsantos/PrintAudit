"""Tests for page_log parsing."""

import pytest

from printaudit.parser import parse_line, parse_page_log


def test_parse_line_basic():
    """Test parsing a basic page_log line."""
    line = (
        "Printer01 alice 12345 [01/Apr/2025:09:03:11 -0300] "
        "total 5 - 192.168.1.1 document.pdf - -"
    )
    entry = parse_line(line)
    assert entry.printer == "Printer01"
    assert entry.user == "alice"
    assert entry.job_id == 12345
    assert entry.pages == 5
    assert entry.host == "192.168.1.1"
    assert entry.job_name == "document.pdf"


def test_parse_line_with_media():
    """Test parsing line with media information."""
    line = (
        "Printer01 bob 12346 [01/Apr/2025:10:00:00 -0300] "
        "total 10 - 192.168.1.2 report.pdf na_letter_8.5x11in one-sided"
    )
    entry = parse_line(line)
    assert entry.pages == 10
    assert entry.media == "na_letter_8.5x11in"
    assert entry.sides == "one-sided"


def test_parse_page_log_file(tmp_path):
    """Test parsing a page_log file."""
    log_file = tmp_path / "page_log"
    log_file.write_text(
        "Printer01 alice 12345 [01/Apr/2025:09:03:11 -0300] "
        "total 5 - 192.168.1.1 doc.pdf - -\n"
        "Printer02 bob 12346 [01/Apr/2025:10:00:00 -0300] "
        "total 10 - 192.168.1.2 report.pdf - -\n"
    )
    entries = list(parse_page_log(log_file))
    assert len(entries) == 2
    assert entries[0].printer == "Printer01"
    assert entries[1].printer == "Printer02"


def test_parse_line_invalid():
    """Test that invalid lines raise ValueError."""
    with pytest.raises(ValueError):
        parse_line("invalid line format")


def test_parse_line_with_billing_code():
    """Test parsing line with billing code."""
    line = (
        "Printer01 alice 12347 [01/Apr/2025:11:00:00 -0300] "
        "total 3 PROJECT123 192.168.1.3 invoice.pdf - -"
    )
    entry = parse_line(line)
    assert entry.pages == 3
    assert entry.billing_code == "PROJECT123"
    assert entry.host == "192.168.1.3"


def test_parse_line_empty_media_sides():
    """Test parsing with empty media and sides (shown as -)."""
    line = (
        "Printer01 charlie 12348 [01/Apr/2025:12:00:00 -0300] "
        "total 1 - 192.168.1.4 doc.pdf - -"
    )
    entry = parse_line(line)
    assert entry.media is None
    assert entry.sides is None


def test_parse_line_job_name_with_spaces():
    """Test parsing job name with spaces."""
    line = (
        "Printer01 diana 12349 [01/Apr/2025:13:00:00 -0300] "
        "total 2 - 192.168.1.5 My Document Name.pdf - -"
    )
    entry = parse_line(line)
    assert entry.job_name == "My Document Name.pdf"
