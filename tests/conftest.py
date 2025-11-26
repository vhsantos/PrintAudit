"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample configuration file."""
    config_file = tmp_path / "printaudit.conf"
    config_file.write_text(
        """[core]
page_log_path=/var/log/cups/page_log
work_start=7
work_end=22
outputs=cli
"""
    )
    return config_file


@pytest.fixture
def sample_page_log(tmp_path):
    """Create a sample page_log file."""
    log_file = tmp_path / "page_log"
    log_file.write_text(
        "Printer01 alice 12345 [01/Apr/2025:09:03:11 -0300] "
        "total 5 - 192.168.1.1 doc.pdf - -\n"
        "Printer02 bob 12346 [01/Apr/2025:10:00:00 -0300] "
        "total 10 - 192.168.1.2 report.pdf - -\n"
    )
    return log_file
