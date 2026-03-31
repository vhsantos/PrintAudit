"""Tests for email output behavior."""

from printaudit.analysis.aggregator import UsageAggregator
from printaudit.config import Config
from printaudit.outputs.base import OutputContext
from printaudit.outputs.email_sender import EmailOutput
from printaudit.parser import parse_line


def _build_report():
    aggregator = UsageAggregator()
    entry = parse_line(
        "Printer01 alice 12345 [01/Apr/2025:09:03:11 -0300] "
        "total 5 - 192.168.1.1 doc.pdf - -"
    )
    aggregator.ingest(entry)
    return aggregator.build_report()


def test_email_body_includes_report_in_body_when_enabled(monkeypatch):
    config = Config()
    config.email.enabled = True
    config.email.recipients = ["ops@example.com"]
    config.email.report_in_body = True

    captured = {}

    def fake_send_report(self, subject, body, attachments):
        captured["subject"] = subject
        captured["body"] = body
        captured["attachments"] = attachments

    monkeypatch.setattr(
        "printaudit.emailer.EmailClient.send_report", fake_send_report
    )

    output = EmailOutput(OutputContext(config=config))
    output.render(_build_report())
    separator = "\n" + ("=" * 72) + "\n"

    assert "PrintAudit summary" in captured["body"]
    assert "Console output" not in captured["body"]
    assert "PrintAudit Summary" in captured["body"]
    assert separator in captured["body"]


def test_email_body_omits_report_in_body_when_disabled(monkeypatch):
    config = Config()
    config.email.enabled = True
    config.email.recipients = ["ops@example.com"]
    config.email.report_in_body = False

    captured = {}

    def fake_send_report(self, subject, body, attachments):
        captured["body"] = body

    monkeypatch.setattr(
        "printaudit.emailer.EmailClient.send_report", fake_send_report
    )

    output = EmailOutput(OutputContext(config=config))
    output.render(_build_report())

    assert "PrintAudit summary" in captured["body"]
    assert "Console output" not in captured["body"]
    assert "PrintAudit Summary" not in captured["body"]
