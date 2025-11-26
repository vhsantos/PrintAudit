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
    # Cost calculation (optional)
    cost_default: float = 0.0
    cost_printer_rates: dict[str, float] = field(default_factory=dict)
    cost_label_rates: dict[str, float] = field(default_factory=dict)
    currency_symbol: str = ""
    currency_code: str = ""


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
    """Load configuration from disk (strictly section-based)."""

    conf_path = discover_config_file(path)
    raw = _read_config_file(conf_path)

    config = Config()

    # Simple key → attribute mappings
    mappings = [
        # [core]
        ("core.page_log_path", "page_log_path", Path),
        ("core.work_start", "work_start", int),
        ("core.work_end", "work_end", int),
        ("core.enabled_sections", "enabled_sections", _split_csv),
        ("core.outputs", "outputs", _split_csv),
        ("core.cli_mode", "cli_mode", str),
        ("core.cli_max_rows", "cli_max_rows", int),
        ("core.csv_dir", "csv_dir", Path),
        ("core.html_path", "html_path", Path),
        # [costs]
        ("costs.default", "cost_default", float),
        ("costs.currency_symbol", "currency_symbol", str),
        ("costs.currency_code", "currency_code", str),
    ]

    for key, attr, caster in mappings:
        if key in raw:
            setattr(config, attr, caster(raw[key]))

    _parse_cost_rates(config, raw)
    _parse_cost_rules(config, raw)
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


def _read_config_file(conf_path: Path) -> dict[str, str]:
    """Read a config file into a flat key/value mapping with section keys."""

    raw: dict[str, str] = {}
    current_section: str | None = None

    with conf_path.open("r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Section header, e.g. [core], [email], [costs], [cost_rules]
            if stripped.startswith("[") and stripped.endswith("]"):
                name = stripped[1:-1].strip().lower()
                current_section = name or None
                continue

            if "=" not in stripped:
                raise ConfigError(
                    f"Invalid config line {lineno} in {conf_path}: {line!r}"
                )

            if current_section is None:
                raise ConfigError(
                    f"Config key outside section at line {lineno} in "
                    f"{conf_path}: {line!r}"
                )

            key, value = stripped.split("=", 1)
            key = key.strip().lower()
            value = value.strip()

            if current_section == "email":
                full_key = f"email.{key}"
            else:
                full_key = f"{current_section}.{key}"

            raw[full_key] = value

    return raw


def _parse_cost_rates(config: Config, raw: dict[str, str]) -> None:
    """Parse printer and label cost rates from the [costs] section."""

    for key, value in raw.items():
        if key.startswith("costs.printer."):
            printer = key.replace("costs.printer.", "").lower()
            if printer:
                config.cost_printer_rates[printer] = float(value)
        elif key.startswith("costs.label."):
            label = key.replace("costs.label.", "").lower()
            if label:
                config.cost_label_rates[label] = float(value)


def _parse_cost_rules(config: Config, raw: dict[str, str]) -> None:
    """Parse cost inference rules from the [cost_rules] section only."""

    prefix = "cost_rules."
    for key, value in raw.items():
        if key.startswith(prefix):
            rule_name = key.replace(prefix, "")
            if rule_name:
                config.cost_inference_rules[rule_name] = value
