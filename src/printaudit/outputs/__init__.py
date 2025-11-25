"""Output module registry."""

# Ensure built-in modules register themselves
from . import cli, csv_writer, email_sender, html_report  # noqa: F401
from .base import OutputContext, OutputModule, get_output_module, list_outputs

__all__ = [
    "OutputContext",
    "OutputModule",
    "get_output_module",
    "list_outputs",
]
