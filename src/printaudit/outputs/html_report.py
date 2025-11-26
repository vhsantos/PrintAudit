"""HTML report generator."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..analysis import AnalysisReport
from .base import OutputModule, register_output


@register_output("html")
class HtmlOutput(OutputModule):
    def render(self, report: AnalysisReport) -> None:
        path = Path(self.context.config.html_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        template = self._build_template(report)
        path.write_text(template, encoding="utf-8")
        self.context.attachments.append(str(path))

    def _build_template(self, report: AnalysisReport) -> str:
        totals = report.totals
        summary = {
            "requests": totals.requests,
            "pages": totals.pages,
            "start": _fmt_dt(totals.first_event),
            "end": _fmt_dt(totals.last_event),
        }
        data = {
            "queue": [vars(stat) for stat in report.queue_stats],
            "users": [vars(stat) for stat in report.user_stats],
            "hourly": [vars(point) for point in report.hourly],
            "daily": [vars(point) for point in report.daily],
            "job_buckets": [vars(bucket) for bucket in report.job_buckets],
            "copy_buckets": [vars(bucket) for bucket in report.copy_buckets],
            "cost": [
                {
                    "label": stat.label,
                    "pages": stat.pages,
                    "amount": stat.amount,
                    "per_user": stat.per_user,
                    "per_queue": stat.per_queue,
                }
                for stat in report.cost_stats
            ],
            "clients": [vars(stat) for stat in report.client_stats],
            "document_types": [vars(stat) for stat in report.document_types],
            "media": [vars(stat) for stat in report.media_stats],
            "duplex": [vars(stat) for stat in report.duplex_stats],
        }
        data_json = json.dumps(data)

        row_limit = self.context.config.cli_max_rows

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>PrintAudit Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; background:#f5f5f5; }}
    section {{ margin-bottom: 2rem; background:#fff; padding:1rem 1.5rem; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
    table {{ width:100%; border-collapse:collapse; margin-top:1rem; }}
    th, td {{ text-align:left; padding:0.35rem 0.5rem; border-bottom:1px solid #ddd; }}
    h1 {{ margin-bottom:0; }}
    canvas {{ max-width: 100%; }}
  </style>
</head>
<body>
  <h1>PrintAudit Executive Summary</h1>
  <p>Requests: {summary["requests"]} | Pages: {summary["pages"]} | Window: {summary["start"]} → {summary["end"]}</p>

  <section>
    <h2>Queue Analysis</h2>
    <canvas id="queueChart" height="160"></canvas>
    {self._table_html(["Queue", "%Req", "%Pages", "Req", "Pages"], data["queue"][:10], ["queue","requests_pct","pages_pct","requests","pages"])}
  </section>

  <section>
    <h2>User Analysis</h2>
    {self._table_html(["User","Requests","Pages","Pages/Request"], data["users"][:row_limit], ["user","requests","pages","pages_per_request"])}
  </section>

  <section>
    <h2>Temporal Analysis</h2>
    <canvas id="hourlyChart" height="160"></canvas>
  </section>

  <section>
    <h2>Job & Copy Distribution</h2>
    {self._table_html(["Bucket","% Requests","Requests"], data["job_buckets"], ["label","pct_requests","request_count"])}
    <h3>Copies</h3>
    {self._table_html(["Bucket","% Requests","Requests"], data["copy_buckets"], ["label","pct_requests","request_count"])}
  </section>

  <section>
    <h2>Cost Analysis</h2>
    {self._table_html(["Label","Pages","Amount","Top Users","Top Queues"], data["cost"], ["label","pages","amount","per_user","per_queue"])}
  </section>

  <section>
    <h2>Media & Clients</h2>
    {self._table_html(["Media","Pages"], data["media"], ["label","pages"])}
    <h3>Clients</h3>
    {self._table_html(["Client","Pages"], data["clients"][:row_limit], ["label","pages"])}
    <h3>Document Types</h3>
    {self._table_html(["Extension","Pages"], data["document_types"], ["label","pages"])}
    <h3>Duplex</h3>
    {self._table_html(["Mode","Pages"], data["duplex"], ["label","pages"])}
  </section>

  <script>
    const data = {data_json};
    function drawBarChart(ctxId, labels, values) {{
      const canvas = document.getElementById(ctxId);
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const width = canvas.width;
      const height = canvas.height;
      const maxVal = Math.max(...values, 1);
      ctx.clearRect(0, 0, width, height);
      const barWidth = width / labels.length;
      ctx.fillStyle = '#4a90e2';
      ctx.font = '10px sans-serif';
      labels.forEach((label, index) => {{
        const value = values[index];
        const barHeight = (value / maxVal) * (height - 20);
        const x = index * barWidth + 5;
        const y = height - barHeight - 10;
        ctx.fillRect(x, y, barWidth - 10, barHeight);
        ctx.fillText(label, x, height - 2);
      }});
    }}
    const queueLabels = data.queue.slice(0, 10).map(row => row.queue);
    const queuePages = data.queue.slice(0, 10).map(row => row.pages);
    drawBarChart('queueChart', queueLabels, queuePages);
    const hourlyLabels = data.hourly.map(point => point.key);
    const hourlyPages = data.hourly.map(point => point.pages);
    drawBarChart('hourlyChart', hourlyLabels, hourlyPages);
  </script>
</body>
</html>
"""  # noqa: E501,E231

    def _table_html(
        self, headers: list[str], rows: list[dict[str, Any]], keys: list[str]
    ) -> str:
        if not rows:
            return "<p>(no data)</p>"
        head = "".join(f"<th>{header}</th>" for header in headers)
        body_rows = []
        for row in rows:
            cells = []
            for key in keys:
                value = row.get(key, "")
                if isinstance(value, list):
                    if value and isinstance(value[0], (list, tuple)):
                        value = ", ".join(f"{a}:{b}" for a, b in value)
                    else:
                        value = ", ".join(str(item) for item in value)
                cells.append(f"<td>{value}</td>")
            body_rows.append("<tr>" + "".join(cells) + "</tr>")
        body = "".join(body_rows)
        return (
            f"<table><thead><tr>{head}</tr></thead>"
            f"<tbody>{body}</tbody></table>"
        )


def _fmt_dt(value: datetime | None) -> str:
    return value.isoformat() if value else "-"
