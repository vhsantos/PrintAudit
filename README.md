# PrintAudit

PrintAudit is a modern Python rewrite of the historical PrintAnalyzer Perl
utility. It ingests the CUPS `page_log`, produces usage, cost, and behavior
reports, and supports modular outputs (CLI, CSV, HTML, email).

## Quick start

```bash
PYTHONPATH=src python3 -m printaudit --config printaudit.conf.sample --dry-run
```

Installers will drop the final binary plus `/etc/printaudit/printaudit.conf`.

### Configuration search order

1. `--config /path/to/printaudit.conf`
2. `$PRINTAUDIT_CONFIG`
3. `/etc/printaudit/printaudit.conf`
4. `/etc/printaudit.conf`
5. `./printaudit.conf`

Copy `printaudit.conf.sample` to `/etc/printaudit/printaudit.conf` and adjust
settings for your environment (log path, work hours, outputs, SMTP).

### Key settings

```
page_log_path=/var/log/cups/page_log
outputs=cli,csv,html,email
cli_mode=rich           # or plain
cli_max_rows=15
csv_dir=/var/spool/printaudit/reports
html_path=/var/spool/printaudit/reports/printaudit.html

# Email (optional)
email.enabled=true
email.smtp_host=mail.example.com
email.smtp_port=587
email.smtp_user=printaudit@example.com
email.smtp_password=secret
email.use_tls=true
email.recipients=ops@example.com,finance@example.com
email.attach_csv=true
email.attach_html=true
```

### Outputs

- `cli`: terminal report (plain/rich)
- `csv`: one CSV per section under `csv_dir`
- `html`: dashboard with lightweight charts
- `email`: uses SMTP settings to send summary plus attachments

### CLI flags

- `--list-outputs` shows registered modules.
- `--start-date` / `--end-date` filter by date range (YYYY-MM-DD).
