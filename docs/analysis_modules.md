# Analysis Modules Reference

This document explains all analysis modules in PrintAudit, what data they provide, and what to expect in the output.

## Quick Start

For basic usage with default settings:

```bash
printaudit -c /etc/printaudit/printaudit.conf
```

For full analysis with cost tracking:

```bash
printaudit -c /etc/printaudit/printaudit.conf --start-date 2025-04-01 --end-date 2025-04-30
```

## Overview

PrintAudit analyzes CUPS `page_log` entries and generates statistics across multiple dimensions. Each analysis module produces specific insights about printing behavior, usage patterns, and costs.

## Executive Summary

**Location**: All outputs
**Data**: `report.totals`

Provides high-level overview of the entire analysis period:

- **Requests**: Total number of print jobs
- **Pages**: Total number of pages printed
- **Window**: Date range of analyzed data (first event → last event)

**Example Output**:

```txt
Requests: 5458 | Pages: 8064 | Window: 2025-04-01 -> 2025-04-30
```

---

## Queue Analysis

**Config Section**: `queue`
**Data**: `report.queue_stats`
**CSV File**: `queue.csv`

Analyzes usage by printer/queue name.

### Metrics

- **Queue**: Printer/queue name
- **Requests**: Number of print jobs
- **Pages**: Total pages printed
- **%Req**: Percentage of total requests
- **%Pages**: Percentage of total pages

### Example Output

**CLI**:

```txt
QUEUE ANALYSIS
Queue          %Req  %Pages  Req   Pages
MP_301         45.2   52.1   2467  4201
RICOH_Aficio   30.1   35.2   1643  2838
MP_201         24.7   12.7   1348  1025
```

**CSV Columns**: `queue,requests_pct,pages_pct,requests,pages`

**Use Cases**:

- Identify most-used printers
- Plan printer capacity
- Detect printer-specific issues

---

## Queue-User Analysis

**Config Section**: `queue_user`
**Data**: `report.queue_user_stats`
**CSV File**: `queue_user.csv`

Cross-analysis of which users print to which queues.

### Metrics

- **Queue**: Printer name
- **User**: Username
- **Pages**: Pages printed by this user on this queue

### Example Output

**CLI**: Not shown by default (use CSV/HTML)

**CSV Columns**: `queue,user,pages`

**Use Cases**:

- Track user-printer relationships
- Identify department-specific printer usage
- Cost allocation by user+printer combination

---

## User Analysis

**Config Section**: `user`
**Data**: `report.user_stats`
**CSV File**: `users.csv`

Per-user printing statistics.

### Metrics

- **User**: Username
- **Requests**: Number of print jobs
- **Pages**: Total pages printed
- **Pages/Request**: Average pages per job

### Example Output

**CLI**:

```txt
USER ANALYSIS
User            Req   Pages  Pages/Req
contabilidad1   234   1793   7.66
rkusch          89    476    5.35
csalas          12    675   56.25
```

**CSV Columns**: `user,requests,pages,pages_per_request`

**Use Cases**:

- Identify heavy users
- Calculate per-user costs
- Detect unusual printing patterns

---

## Temporal Analysis

**Config Section**: `temporal`
**Data**: `report.hourly`, `report.daily`
**CSV Files**: `hourly.csv`, `daily.csv`

Time-based usage patterns showing when printing occurs.

### Hourly Analysis

**Metrics**:

- **Hour**: Hour of day (00-23)
- **Requests**: Print jobs in this hour
- **Pages**: Pages printed in this hour
- **Within Hours**: Whether hour falls within `work_start`-`work_end`

**Example Output**:

**CLI**:

```txt
TEMPORAL ANALYSIS
Hour usage:
07:00:  5 req /   5 pages !
08:00: 50 req /  63 pages !
09:00: 654 req / 843 pages
10:00: 902 req / 1136 pages
...
```

(`!` indicates outside work hours)

**CSV Columns**: `hour,requests,pages`

**HTML**: Bar chart showing hourly distribution

### Daily Analysis

**Metrics**:

- **Date**: Date (YYYY-MM-DD)
- **Requests**: Print jobs on this date
- **Pages**: Pages printed on this date

**Example Output**:

**CLI**:

```txt
Daily usage:
2025-04-01: 234 req / 1234 pages
2025-04-02: 198 req / 987 pages
...
```

**CSV Columns**: `date,requests,pages`

**Use Cases**:

- Identify peak usage times
- Plan maintenance windows
- Detect after-hours printing
- Track daily trends

---

## Job Analysis

**Config Section**: `job`
**Data**: `report.job_buckets`, `report.copy_buckets`
**CSV Files**: `job_buckets.csv`, `copy_buckets.csv`

Distribution analysis of job sizes and copy counts.

### Job Size Buckets

Groups jobs by number of pages per job:

- `0-10`, `11-20`, `21-30`, ..., `100+`

**Metrics**:

- **Bucket**: Page count range
- **%Req**: Percentage of requests in this bucket
- **Requests**: Number of jobs in this bucket

**Example Output**:

**CLI**:

```txt
JOB ANALYSIS
Job Size  %Req   Requests
0-10      45.2   2467
11-20     30.1   1643
21-30     15.3    835
...
```

**CSV Columns**: `bucket,pct_requests,requests`

### Copy Buckets

Groups jobs by number of copies per job:

- `1`, `2-5`, `6-10`, `11-20`, `21+`

**Metrics**:

- **Copies**: Copy count range
- **%Req**: Percentage of requests
- **Requests**: Number of jobs

**Example Output**:

**CLI**:

```txt
Copies:
Copies  %Req   Requests
1       78.5   4285
2-5     18.2    993
6-10     2.8    152
...
```

**CSV Columns**: `bucket,pct_requests,requests`

**Use Cases**:

- Understand typical job sizes
- Identify bulk printing
- Plan for high-volume jobs

---

## Cost Analysis

**Config Section**: `cost`
**Data**: `report.cost_stats`
**CSV File**: `cost.csv`
**Requires**: `[costs]` and/or `[cost_rules]` configuration

Department/label-based cost allocation with currency-agnostic calculation.

### Configuration

Cost calculation uses three rate sources (in precedence order):

1. **Label-specific rates** (`label.contabilidad=0.03`)
2. **Printer-specific rates** (`printer.MP_301=0.01`)
3. **Default rate** (`default=0.02`)

Cost labels are assigned via `[cost_rules]` section mapping users/queues to labels.

### Metrics

- **Label**: Cost center/department name
- **Pages**: Total pages for this label
- **Amount**: Calculated cost (pages × rate)
- **Top Users**: Top users contributing to this label
- **Top Queues**: Top printers contributing to this label

### Example Output

**CLI**:

```
COST ANALYSIS
Label        Pages  Cost      Top Users
contabilidad 4418   CLP$110,450  contabilidad1:1793, contabilidad3:1094
caja         675    CLP$20,250   csalas:675
sistemas     448    CLP$0        isaavedra:448
unassigned   2279   CLP$0        rkusch:476, jcardenas:466
```

**CSV Columns**: `label,pages,amount,top_users,top_queues`

**HTML**: Table with currency-formatted amounts

**Use Cases**:

- Department cost allocation
- Budget planning
- Cost center reporting
- Printer cost analysis

### Cost Label Assignment

Jobs are assigned to cost labels based on `[cost_rules]`:

```ini
[cost_rules]
contabilidad=contabilidad1,contabilidad2,contabilidad3
caja=csalas
```

If no rule matches, jobs are assigned to `"unassigned"`.

---

## Media Analysis

**Config Section**: `media` (implicit)
**Data**: `report.media_stats`
**CSV File**: `media.csv`

Paper/media type usage from CUPS job attributes.

### Metrics

- **Media**: Media type name (e.g., `na_letter_8.5x11in`, `a4`)
- **Pages**: Pages printed on this media type

### Example Output

**CLI**:

```txt
MEDIA & CLIENTS
Media                    Pages
na_letter_8.5x11in      6543
a4                       1521
```

**CSV Columns**: `media,pages`

**Note**: If CUPS doesn't report media type, shows as `"unknown"`.

**Use Cases**:

- Paper inventory planning
- Media cost analysis
- Standardization tracking

---

## Client Analysis

**Config Section**: `clients` (implicit)
**Data**: `report.client_stats`
**CSV File**: `clients.csv`

Source hostname/IP address tracking.

### Metrics

- **Client**: Hostname or IP address
- **Pages**: Pages printed from this client

### Example Output

**CLI**:

```txt
Clients:
Client         Pages
192.168.10.35  1234
192.168.10.29   987
workstation-01  654
```

**CSV Columns**: `client,pages`

**Use Cases**:

- Identify source machines
- Network printing analysis
- Security auditing

---

## Document Types Analysis

**Config Section**: `document_types` (implicit)
**Data**: `report.document_types`
**CSV File**: `document_types.csv`

File extension analysis from job names.

### Metrics

- **Extension**: File extension (e.g., `pdf`, `xlsx`, `docx`)
- **Pages**: Pages printed from this document type

### Example Output

**CLI**:

```txt
Document Types:
Extension  Pages
pdf        3456
xlsx       2341
frx        1234
docx        543
```

**CSV Columns**: `extension,pages`

**Use Cases**:

- Application usage tracking
- Document type distribution
- Software license planning

---

## Duplex Analysis

**Config Section**: `duplex` (implicit)
**Data**: `report.duplex_stats`
**CSV File**: `duplex.csv`

Two-sided vs. one-sided printing analysis.

### Metrics

- **Mode**: `"duplex"` (two-sided), `"simplex"` (one-sided), or `"unknown"`
- **Pages**: Pages printed in this mode

### Example Output

**CLI**:

```txt
Duplex:
Mode     Pages
unknown  8064
```

**CSV Columns**: `mode,pages`

**Note**: Shows `"unknown"` when CUPS doesn't report duplex mode (common with many drivers). Will show `"duplex"` or `"simplex"` when available.

**Use Cases**:

- Paper savings analysis
- Duplex policy compliance
- Environmental reporting

---

## Enabling/Disabling Sections

Control which analysis sections are generated via `enabled_sections`:

```ini
[core]
enabled_sections=queue,queue_user,user,temporal,job,cost
```

Available sections:

- `queue` - Queue analysis
- `queue_user` - Queue-user cross-analysis
- `user` - User analysis
- `temporal` - Hourly/daily analysis
- `job` - Job size and copy distribution
- `cost` - Cost analysis (requires `[costs]` config)

Sections not listed are still computed but may not appear in CLI output (CSV/HTML always include all data).

---

## Output Format Differences

### CLI Output

- Shows top N rows (controlled by `cli_max_rows`)
- Rich formatting available (`cli_mode=rich`)
- Sections can be enabled/disabled
- Focuses on most important data

### CSV Output

- One file per analysis section
- All data included (no row limits)
- Machine-readable format
- Suitable for import into spreadsheets/databases

### HTML Output

- Interactive dashboard
- Charts for queue and hourly analysis
- All sections in tables
- Professional presentation format

### Email Output

- Text summary in body
- Attachments: CSV and/or HTML files
- Configurable subject and sender

---

## Understanding the Data

### Percentages

All percentage fields (`%Req`, `%Pages`, `pct_requests`) are calculated relative to the total for that dimension.

### Date Filtering

When using `--start-date` and `--end-date`, only entries within that range are analyzed. The "Window" in the summary reflects the actual date range of data found.

### Work Hours

The `work_start` and `work_end` settings (default 7-22) are used to:

- Mark hours in temporal analysis as within/outside work hours
- Help identify after-hours printing patterns

### Cost Calculation

Costs are calculated as: `pages × rate`

The rate used follows precedence:

1. Label-specific rate (if job matches a cost rule label)
2. Printer-specific rate (if configured for the queue)
3. Default rate (if configured)

If no rates are configured, all costs show as `0.0`.

---

## Configuration Examples

### Basic Cost Allocation

```ini
[costs]
default=0.02
currency_symbol=CLP$

[cost_rules]
accounting=contabilidad1,contabilidad2,contabilidad3
sales=csalas
```

### Advanced Cost Setup

```ini
[costs]
default=0.05
currency_symbol=$
printer.MP_301=0.03
printer.RICOH_Aficio_MP_2000=0.08
label.accounting=0.02

[cost_rules]
accounting=contabilidad1,contabilidad2
sales=csalas
it=rkusch,jcardenas
```

## Common Use Cases

### Department Cost Allocation

1. Map users to departments in `[cost_rules]`
2. Set department rates in `[costs] label.*`
3. Run monthly: `printaudit -c printaudit.conf`

### Printer Utilization Monitoring

1. Enable `queue` and `temporal` sections
2. Analyze peak usage hours and printer loads
3. Plan maintenance and upgrades

### User Behavior Analysis

1. Enable `user` and `job` sections
2. Identify heavy users and typical job sizes
3. Set printing policies and quotas

## Reading the Reports

### Executive Summary

- **Requests**: Total print jobs (measure of printer load)
- **Pages**: Total paper usage (measure of consumables)
- **Window**: Data coverage period

### Queue Analysis

- Focus on printers with high `%Pages` for cost optimization
- High `%Req` but low `%Pages` indicates many small jobs

### User Analysis

- High `Pages/Request` may indicate bulk printing or reports
- Compare user patterns to identify training opportunities

### Temporal Analysis

- `!` marks indicate after-hours printing
- Peak hours help plan printer maintenance

## Performance Tips

- For large log files (>100MB), use specific date ranges with `--start-date` and `--end-date`
- Disable unused sections in `enabled_sections` to reduce processing time
- CSV output is fastest for data processing
- HTML output includes charts but takes longer to generate

## Troubleshooting

### All Duplex Shows "unknown"

This is normal when printer drivers don't report duplex mode to CUPS. The `sides` field in `page_log` will be `-`, which PrintAudit correctly interprets as unknown.

### Cost Shows Zero

**Check**:

1. `[costs]` section has `default` rate or printer/label rates
2. `[cost_rules]` maps users/queues to labels (if using label rates)
3. Jobs match the cost rules (case-sensitive matching)

**Example**: If users show in "unassigned", add missing users to `[cost_rules]` sections.

### Cost Calculation Examples

**Scenario**: All costs show zero

**Check**:

- `[costs] default` rate is set
- `[cost_rules]` entries match actual usernames
- Usernames in logs match rule patterns (case-sensitive)

**Scenario**: Some users show in "unassigned"

**Fix**: Add missing users to `[cost_rules]` sections:

```ini
[cost_rules]
accounting=contabilidad1,contabilidad2,contabilidad3,contabilidad4
```

### Missing Data in Reports

- Verify `page_log_path` points to valid CUPS page_log
- Check file permissions
- Ensure date range includes data (`--start-date` / `--end-date`)

### Sections Not Appearing

- Verify section name in `enabled_sections` matches exactly
- Check that section is available (some require configuration)
