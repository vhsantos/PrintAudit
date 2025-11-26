# PrintAudit

**PrintAudit** is a modern Python rewrite of the historical PrintAnalyzer Perl utility. It ingests CUPS `page_log` files, produces comprehensive usage, cost, and behavior reports, and supports modular outputs (CLI, CSV, HTML, email).

## Features

- **Comprehensive Analysis**: Queue usage, user activity, temporal patterns, cost allocation, and more
- **Cost Tracking**: Currency-agnostic cost calculation with configurable rates per printer, department, or label
- **Flexible Outputs**: Multiple output formats (CLI, CSV, HTML, email) with plugin architecture
- **Date Filtering**: Analyze specific time ranges with `--start-date` and `--end-date`
- **Work Hours Detection**: Identify printing activity within configured business hours
- **Modular Design**: Easy to extend with custom output modules

## Installation

### From Source

```bash
git clone https://github.com/vhsantos/PrintAudit.git
cd printaudit
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Quick Test

```bash
PYTHONPATH=src python3 -m printaudit --config printaudit.conf.sample --dry-run
```

## Configuration

### Configuration File Search Order

PrintAudit searches for configuration files in this order:

1. `--config /path/to/printaudit.conf` (command-line override)
2. `$PRINTAUDIT_CONFIG` (environment variable)
3. `/etc/printaudit/printaudit.conf`
4. `/etc/printaudit.conf`
5. `./printaudit.conf` (current directory)

### Basic Setup

1. Copy the sample configuration:

   ```bash
   sudo cp printaudit.conf.sample /etc/printaudit/printaudit.conf
   ```

2. Edit `/etc/printaudit/printaudit.conf` and adjust:
   - `page_log_path`: Path to your CUPS page_log file
   - `work_start` / `work_end`: Business hours (7-22 = 7 AM to 10 PM)
   - `outputs`: Comma-separated list of output modules
   - `enabled_sections`: Which analysis sections to include

### Configuration Sections

#### `[core]` - Main Settings

```ini
[core]
page_log_path=/var/log/cups/page_log
work_start=7
work_end=22
enabled_sections=queue,queue_user,user,temporal,job,cost
outputs=cli,csv,html,email
cli_mode=rich              # or "plain"
cli_max_rows=15
csv_dir=/var/spool/printaudit/reports
html_path=/var/spool/printaudit/reports/printaudit.html
html_use_chartjs=false     # Use Chart.js for graphs (optional)
```

#### `[email]` - Email Delivery

```ini
[email]
enabled=true
smtp_host=mail.example.com
smtp_port=587
smtp_user=printaudit@example.com
smtp_password=secret
use_tls=true
recipients=ops@example.com,finance@example.com
subject=PrintAudit Report
from=printaudit@example.com
attach_csv=true
attach_html=true
```

#### `[costs]` - Cost Calculation

```ini
[costs]
# Default cost per page (unitless, use your local currency)
default=0.02

# Currency display settings (optional)
currency_symbol=CLP$
currency_code=CLP

# Printer-specific rates (optional)
printer.MP_301=0.01
printer.RICOH_Aficio_MP_2000=0.05

# Department/label-specific rates (optional)
label.contabilidad=0.03
label.marketing=0.05
label.IT=0.04
```

#### `[cost_rules]` - Cost Label Mapping

```ini
[cost_rules]
# Map users/queues to cost labels for department allocation
contabilidad=contabilidad1,contabilidad2,contabilidad3
caja=csalas
plataforma=jrogel,cskarmeta,csaavedra
sistemas=isaavedra
```

## Usage

### Basic Command

```bash
printaudit
```

### With Date Range

```bash
printaudit --start-date 2025-04-01 --end-date 2025-04-30
```

### Override Outputs

```bash
printaudit --outputs cli,html
```

### List Available Output Modules

```bash
printaudit --list-outputs
```

### Dry Run (Test Configuration)

```bash
printaudit --dry-run
```

## Output Modules

PrintAudit supports multiple output formats:

- **`cli`**: Terminal report with plain or rich formatting
- **`csv`**: One CSV file per analysis section in `csv_dir`
- **`html`**: Interactive HTML dashboard with charts
- **`email`**: SMTP delivery of summary and attachments

See [Creating Output Modules](docs/creating_output_modules.md) for extending with custom formats.

## Analysis Modules

PrintAudit provides comprehensive analysis across multiple dimensions:

- **Queue Analysis**: Usage by printer/queue with percentages
- **User Analysis**: Per-user statistics with pages per request
- **Temporal Analysis**: Hourly and daily usage patterns
- **Job Analysis**: Distribution of job sizes and copy counts
- **Cost Analysis**: Department/label-based cost allocation
- **Media Analysis**: Paper/media type usage
- **Client Analysis**: Source hostname tracking
- **Document Types**: File extension analysis
- **Duplex Analysis**: Two-sided vs. one-sided printing

See [Analysis Modules Documentation](docs/analysis_modules.md) for detailed explanations and expected outputs.

## Command-Line Options

```bash
  -c, --config PATH       Path to configuration file
  -o, --outputs LIST     Comma-separated output modules override
  --cli-mode MODE        CLI renderer style (plain/rich)
  --start-date DATE      Filter start date (YYYY-MM-DD)
  --end-date DATE        Filter end date (YYYY-MM-DD)
  --dry-run              Test configuration without running
  --list-outputs         List available output modules
  -h, --help             Show help message
```

## Examples

### Generate All Reports

```bash
printaudit
```

This creates:

- CLI output to terminal
- CSV files in `csv_dir`
- HTML report at `html_path`
- Email delivery (if enabled)

### Monthly Report

```bash
printaudit --start-date 2025-04-01 --end-date 2025-04-30
```

### HTML Only

```bash
printaudit --outputs html
```

## Requirements

- Python 3.10+
- CUPS `page_log` file access
- Optional: SMTP server for email delivery

## Dependencies

- `rich>=13.0.0` - Enhanced terminal output
- `click>=8.0.0` - Command-line interface

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see the documentation for:

- [Creating Output Modules](docs/creating_output_modules.md)
- [Analysis Modules Reference](docs/analysis_modules.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/vhsantos/PrintAudit/issues)
- **Repository**: [GitHub Repository](https://github.com/vhsantos/PrintAudit)
