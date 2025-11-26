# Creating a New Output Module

This guide explains how to create a new output module for PrintAudit (e.g., XLS, PDF, JSON, etc.).

## Overview

PrintAudit uses a **plugin-style registration system** for output modules. Each module:

1. Inherits from `OutputModule`
2. Implements the `render()` method
3. Registers itself with a unique name
4. Gets automatically discovered and used

## Step-by-Step Workflow

### Step 1: Create Your Module File

Create a new file in `src/printaudit/outputs/`:

```python
# src/printaudit/outputs/xls_writer.py
"""Excel export module."""

from __future__ import annotations

from pathlib import Path

from ..analysis import AnalysisReport
from .base import OutputModule, register_output


@register_output("xls")
class XlsOutput(OutputModule):
    def render(self, report: AnalysisReport) -> None:
        # Your implementation here
        pass
```

### Step 2: Implement the `render()` Method

The `render()` method receives an `AnalysisReport` object with all the analyzed data:

```python
def render(self, report: AnalysisReport) -> None:
    # Access configuration
    output_path = Path(self.context.config.html_path)  # or custom config

    # Access report data
    totals = report.totals  # TotalStats object
    queue_stats = report.queue_stats  # List[QueueStat]
    user_stats = report.user_stats  # List[UserStat]
    cost_stats = report.cost_stats  # List[CostStat]
    hourly = report.hourly  # List[TemporalPoint]
    # ... etc (see AnalysisReport for full list)

    # Generate your output
    # ...

    # Register generated file (if applicable)
    self.context.attachments.append(str(output_path))
```

### Step 3: Register Your Module

Import your module in `src/printaudit/outputs/__init__.py`:

```python
# src/printaudit/outputs/__init__.py
from . import cli, csv_writer, email_sender, html_report, xls_writer  # noqa: F401
```

**Important**: The import statement is what triggers the `@register_output()` decorator to run, registering your module.

### Step 4: Add Configuration (Optional)

If your module needs configuration, add fields to `Config` in `src/printaudit/config.py`:

```python
@dataclass
class Config:
    # ... existing fields ...
    xls_path: Path = Path("/var/spool/printaudit/reports/printaudit.xls")
```

Then parse it in `parse_config()`:

```python
mappings = [
    # ... existing mappings ...
    ("core.xls_path", "xls_path", Path),
]
```

### Step 5: Use Your Module

Add your module name to the `outputs` config:

```ini
[core]
outputs=cli,csv,html,xls
```

## Available Report Data

The `AnalysisReport` object contains:

```python
@dataclass
class AnalysisReport:
    totals: TotalStats  # requests, pages, first_event, last_event
    queue_stats: list[QueueStat]  # per-queue statistics
    queue_user_stats: list[QueueUserStat]  # queue+user combinations
    user_stats: list[UserStat]  # per-user statistics
    hourly: list[TemporalPoint]  # hourly breakdown
    daily: list[TemporalPoint]  # daily breakdown
    job_buckets: list[BucketStat]  # job size distribution
    copy_buckets: list[BucketStat]  # copy count distribution
    cost_stats: list[CostStat]  # cost analysis by label
    client_stats: list[SimpleStat]  # client hostnames
    document_types: list[SimpleStat]  # file extensions
    media_stats: list[SimpleStat]  # paper/media types
    duplex_stats: list[SimpleStat]  # duplex/simplex modes
```

## Accessing Configuration

Your module has access to:

```python
self.context.config  # Full Config object
self.context.attachments  # List to append generated file paths
self.context.stdout  # stdout for CLI output (if needed)
```

## Example: Simple JSON Output

```python
"""JSON export module."""

from __future__ import annotations

import json
from pathlib import Path

from ..analysis import AnalysisReport
from .base import OutputModule, register_output


@register_output("json")
class JsonOutput(OutputModule):
    def render(self, report: AnalysisReport) -> None:
        path = Path(self.context.config.html_path).with_suffix(".json")
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "totals": {
                "requests": report.totals.requests,
                "pages": report.totals.pages,
                "first_event": report.totals.first_event.isoformat(),
                "last_event": report.totals.last_event.isoformat(),
            },
            "queues": [
                {
                    "queue": stat.queue,
                    "requests": stat.requests,
                    "pages": stat.pages,
                }
                for stat in report.queue_stats
            ],
            # ... add more sections as needed
        }

        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.context.attachments.append(str(path))
```

## Example: Image/Chart Output

```python
"""PNG chart export module."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..analysis import AnalysisReport
from .base import OutputModule, register_output


@register_output("png")
class PngOutput(OutputModule):
    def render(self, report: AnalysisReport) -> None:
        path = Path(self.context.config.html_path).with_suffix(".png")
        path.parent.mkdir(parents=True, exist_ok=True)

        # Create image
        img = Image.new("RGB", (800, 600), color="white")
        draw = ImageDraw.Draw(img)

        # Draw chart from report.queue_stats
        # ... your drawing logic ...

        img.save(path)
        self.context.attachments.append(str(path))
```

## Testing Your Module

1. Add your module name to config:

   ```ini
   [core]
   outputs=cli,your_module_name
   ```

2. Run PrintAudit:

   ```bash
   printaudit -c your_config.conf
   ```

3. Check that your output is generated and listed in attachments.

## Key Points

- **Registration is automatic**: Just import your module in `__init__.py`
- **Name must be unique**: The `@register_output("name")` name is what users put in config
- **Attachments**: Append file paths to `self.context.attachments` so they can be emailed/listed
- **Configuration**: Access via `self.context.config`
- **Report data**: All analyzed data is in the `AnalysisReport` object

## Current Built-in Modules

- `cli` - Command-line output (plain/rich)
- `csv` - CSV file exports
- `html` - HTML report with charts
- `email` - Email delivery (runs last automatically)

You can create any format: XLS, PDF, JSON, PNG, JPG, XML, etc.!
