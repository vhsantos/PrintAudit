"""SMTP helper for PrintAudit report delivery."""

from __future__ import annotations

import smtplib
from collections.abc import Sequence
from email.message import EmailMessage
from pathlib import Path

from .config import EmailSettings


class EmailDeliveryError(RuntimeError):
    """Raised when sending email reports fails."""


class EmailClient:
    """Thin SMTP wrapper using :class:`EmailSettings`."""

    def __init__(self, settings: EmailSettings):
        self.settings = settings

    def send_report(
        self,
        subject: str,
        body: str,
        attachments: Sequence[Path] | None = None,
    ) -> None:
        if not self.settings.enabled:
            raise EmailDeliveryError(
                "Email delivery disabled in configuration."
            )
        if not self.settings.recipients:
            raise EmailDeliveryError(
                "Email enabled but no recipients configured."
            )

        message = EmailMessage()
        message["Subject"] = subject
        from_addr = (
            self.settings.from_address
            or self.settings.smtp_user
            or "printaudit@localhost"
        )
        message["From"] = from_addr
        message["To"] = ", ".join(self.settings.recipients)
        message.set_content(body)

        for path in attachments or []:
            data = path.read_bytes()
            message.add_attachment(
                data,
                maintype="application",
                subtype="octet-stream",
                filename=path.name,
            )

        self._send(message)

    def _send(self, message: EmailMessage) -> None:
        try:
            with smtplib.SMTP(
                self.settings.smtp_host or "localhost",
                self.settings.smtp_port,
                timeout=30,
            ) as server:
                if self.settings.use_tls:
                    server.starttls()
                if self.settings.smtp_user or self.settings.smtp_password:
                    server.login(
                        self.settings.smtp_user,
                        self.settings.smtp_password,
                    )
                server.send_message(message)
        except OSError as exc:  # pragma: no cover - network dependent
            raise EmailDeliveryError(str(exc)) from exc
