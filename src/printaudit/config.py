"""Configuration handling for PrintAudit."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when the configuration file cannot be parsed or found."""


DEFAULT_CONF_PATHS: list[Path] = [
    Path("/etc/printaudit/printaudit.conf"),
    Path("/etc/printaudit.conf"),
    Path.cwd() / "printaudit.conf",
]


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class EmailSettings:
    enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    use_tls: bool = False
    recipients: list[str] = field(default_factory=list)
    attach_csv: bool = False
    attach_html: bool = False


@dataclass
class Config:
    page_log_path: Path = Path("/var/log/cups/page_log")
    work_start: int = 7
    work_end: int = 22
    enabled_sections: list[str] = field(
        default_factory=lambda: [
            "queue",
            "queue_user",
            "user",
            "temporal",
            "job",
            "cost",
        ]
    )
    outputs: list[str] = field(default_factory=lambda: ["cli"])
    cli_mode: str = "rich"  # plain|rich
    cli_max_rows: int = 15
    csv_dir: Path = Path("./reports")
    html_path: Path = Path("./reports/printaudit.html")
    cost_inference_rules: dict[str, str] = field(default_factory=dict)
    email: EmailSettings = field(default_factory=EmailSettings)


def discover_config_file(explicit_path: Path | None = None) -> Path:
    """Return the first readable configuration file."""

    candidates: Iterable[Path]
    if explicit_path:
        candidates = [explicit_path]
    else:
        env_path = os.getenv("PRINTAUDIT_CONFIG")
        candidates = [Path(env_path)] if env_path else DEFAULT_CONF_PATHS

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise ConfigError(
        "No configuration file found. Searched: "
        + ", ".join(str(p) for p in candidates)
    )


def parse_config(path: Path | None = None) -> Config:
    """Load configuration from disk."""

    conf_path = discover_config_file(path)
    raw: dict[str, str] = {}

    # Lightweight parser with optional [section] support.
    #
    # - Lines before any section behave like the legacy flat key=value format.
    # - Lines under [email] are exposed as "email.<key>" to preserve the
    #   existing EmailSettings mapping.
    # - Other sections use "section.key" as the raw key.
    current_section: str | None = None
    with conf_path.open("r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Section header, e.g. [core], [email], [costs]
            if stripped.startswith("[") and stripped.endswith("]"):
                name = stripped[1:-1].strip().lower()
                current_section = name or None
                continue

            if "=" not in stripped:
                raise ConfigError(
                    f"Invalid config line {lineno} in {conf_path}: {line!r}"
                )
            key, value = stripped.split("=", 1)
            key = key.strip().lower()
            value = value.strip()

            if current_section is None:
                full_key = key
            elif current_section == "email":
                full_key = f"email.{key}"
            else:
                full_key = f"{current_section}.{key}"

            raw[full_key] = value

    config = Config()
    if "page_log_path" in raw:
        config.page_log_path = Path(raw["page_log_path"])
    if "work_start" in raw:
        config.work_start = int(raw["work_start"])
    if "work_end" in raw:
        config.work_end = int(raw["work_end"])
    if "enabled_sections" in raw:
        config.enabled_sections = _split_csv(raw["enabled_sections"])
    if "outputs" in raw:
        config.outputs = _split_csv(raw["outputs"])
    if "cli_mode" in raw:
        config.cli_mode = raw["cli_mode"]
    if "cli_max_rows" in raw:
        config.cli_max_rows = int(raw["cli_max_rows"])
    if "csv_dir" in raw:
        config.csv_dir = Path(raw["csv_dir"])
    if "html_path" in raw:
        config.html_path = Path(raw["html_path"])

    for key, value in raw.items():
        if key.startswith("cost_rule."):
            _, _, rule_name = key.partition(".")
            config.cost_inference_rules[rule_name] = value

    _load_email_settings(config.email, raw)

    return config


def _load_email_settings(email: EmailSettings, raw: dict[str, str]) -> None:
    mapping = {
        "email.enabled": ("enabled", _bool),
        "email.smtp_host": ("smtp_host", str),
        "email.smtp_port": ("smtp_port", int),
        "email.smtp_user": ("smtp_user", str),
        "email.smtp_password": ("smtp_password", str),
        "email.use_tls": ("use_tls", _bool),
        "email.recipients": ("recipients", _split_csv),
        "email.attach_csv": ("attach_csv", _bool),
        "email.attach_html": ("attach_html", _bool),
    }

    for key, (attr, caster) in mapping.items():
        if key in raw:
            setattr(email, attr, caster(raw[key]))
