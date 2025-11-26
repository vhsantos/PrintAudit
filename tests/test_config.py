"""Tests for configuration parsing."""

import pytest

from printaudit.config import Config, ConfigError, parse_config


def test_config_defaults():
    """Test that Config has sensible defaults."""
    config = Config()
    assert config.work_start == 7
    assert config.work_end == 22
    assert config.cost_default == 0.0
    assert config.currency_symbol == ""
    assert config.currency_code == ""


def test_parse_config_missing_file(tmp_path):
    """Test that missing config file raises ConfigError."""
    with pytest.raises(ConfigError):
        parse_config(tmp_path / "nonexistent.conf")


def test_parse_config_section_based(tmp_path):
    """Test parsing section-based configuration."""
    config_file = tmp_path / "test.conf"
    config_file.write_text(
        """[core]
page_log_path=/var/log/cups/page_log
work_start=8
work_end=20
outputs=cli,csv
"""
    )
    config = parse_config(config_file)
    assert config.work_start == 8
    assert config.work_end == 20
    assert config.outputs == ["cli", "csv"]


def test_parse_config_cost_settings(tmp_path):
    """Test parsing cost configuration."""
    config_file = tmp_path / "test.conf"
    config_file.write_text(
        """[core]
page_log_path=/var/log/cups/page_log

[costs]
default=0.02
currency_symbol=$
currency_code=USD
"""
    )
    config = parse_config(config_file)
    assert config.cost_default == 0.02
    assert config.currency_symbol == "$"
    assert config.currency_code == "USD"


def test_parse_config_cost_rules(tmp_path):
    """Test parsing cost rules."""
    config_file = tmp_path / "test.conf"
    config_file.write_text(
        """[core]
page_log_path=/var/log/cups/page_log

[cost_rules]
accounting=accounting1,accounting2
sales=bob
"""
    )
    config = parse_config(config_file)
    assert "accounting" in config.cost_inference_rules
    assert "sales" in config.cost_inference_rules
    assert (
        "accounting1,accounting2" in config.cost_inference_rules["accounting"]
    )


def test_parse_config_printer_rates(tmp_path):
    """Test parsing printer-specific rates."""
    config_file = tmp_path / "test.conf"
    config_file.write_text(
        """[core]
page_log_path=/var/log/cups/page_log

[costs]
printer.Printer01=0.01
printer.Printer02=0.05
"""
    )
    config = parse_config(config_file)
    assert "printer01" in config.cost_printer_rates
    assert config.cost_printer_rates["printer01"] == 0.01
    assert config.cost_printer_rates["printer02"] == 0.05
