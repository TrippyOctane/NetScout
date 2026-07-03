"""Export NetScout scan results to CSV and JSON files."""

from __future__ import annotations

import csv
import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from netscout.ports import get_service_name
from netscout.scanner import ScanResult


EXPORT_FIELDS = (
    "ip_address",
    "hostname",
    "mac_address",
    "vendor",
    "device_type",
    "status",
    "open_ports",
)


def _timestamp() -> str:
    """Return a timestamp that is safe to use in filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _format_export_time(export_time: datetime) -> str:
    """Return a human-readable timestamp for reports."""
    return export_time.strftime("%Y-%m-%d %H:%M:%S")


def _result_to_row(result: ScanResult) -> dict[str, object]:
    """Convert one ScanResult into simple values for export files."""
    return {
        "ip_address": str(result.ip_address),
        "hostname": result.hostname,
        "mac_address": result.mac_address,
        "vendor": result.vendor,
        "device_type": result.device_type,
        "status": result.status,
        "open_ports": result.open_ports,
    }


def _write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    """Write scan result rows to a CSV file."""
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPORT_FIELDS)
        writer.writeheader()

        for row in rows:
            csv_row = row.copy()
            # CSV cells are plain text, so store open ports as comma-separated
            # port numbers while JSON keeps them as a real list.
            csv_row["open_ports"] = ", ".join(
                str(port) for port in row["open_ports"]
            )
            writer.writerow(csv_row)


def _write_json(rows: list[dict[str, object]], output_path: Path) -> None:
    """Write scan result rows to a JSON file."""
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(rows, json_file, indent=2)
        json_file.write("\n")


def _format_open_ports_for_html(open_ports: object) -> str:
    """Format open ports with service names for the HTML table."""
    if not isinstance(open_ports, list) or not open_ports:
        return "None"

    return ", ".join(
        f"{port} ({get_service_name(port)})"
        for port in open_ports
        if isinstance(port, int)
    )


def _device_inventory(rows: list[dict[str, object]]) -> list[tuple[str, int]]:
    """Count devices by type, with Unknown listed last."""
    inventory = Counter(str(row.get("device_type", "Unknown")) for row in rows)
    device_types = sorted(
        device_type
        for device_type in inventory
        if device_type != "Unknown"
    )
    if "Unknown" in inventory:
        device_types.append("Unknown")

    return [
        (device_type, inventory[device_type])
        for device_type in device_types
    ]


def _write_html(
    rows: list[dict[str, object]],
    output_path: Path,
    report_info: dict[str, Any],
    export_timestamp: str,
) -> None:
    """Write a clean standalone HTML scan report."""
    summary = report_info.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    version = html.escape(str(report_info.get("version", "Unknown")))
    detected_network = html.escape(str(report_info.get("detected_network", "Unknown")))
    local_ip = html.escape(str(report_info.get("local_ip", "Not available")))
    gateway = html.escape(str(report_info.get("gateway", "Not available")))

    result_rows = []
    for row in rows:
        result_rows.append(
            "          <tr>"
            f"<td>{html.escape(str(row['ip_address']))}</td>"
            f"<td>{html.escape(str(row['hostname']))}</td>"
            f"<td>{html.escape(str(row['mac_address']))}</td>"
            f"<td>{html.escape(str(row['vendor']))}</td>"
            f"<td>{html.escape(str(row['device_type']))}</td>"
            f"<td>{html.escape(str(row['status']))}</td>"
            f"<td>{html.escape(_format_open_ports_for_html(row['open_ports']))}</td>"
            "</tr>"
        )

    if not result_rows:
        result_rows.append(
            '          <tr><td colspan="7" class="empty">No live hosts found.</td></tr>'
        )

    inventory_items = [
        f"          <li><span>{html.escape(device_type)}</span><strong>{count}</strong></li>"
        for device_type, count in _device_inventory(rows)
    ]
    if not inventory_items:
        inventory_items.append("          <li><span>No devices found.</span><strong>0</strong></li>")

    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NetScout Scan Report</title>
  <style>
    body {{
      margin: 0;
      background: #f4f7fb;
      color: #1f2937;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px;
    }}
    h1, h2 {{
      margin: 0 0 12px;
      color: #111827;
    }}
    h1 {{
      font-size: 30px;
    }}
    h2 {{
      font-size: 20px;
      border-bottom: 1px solid #d8e0ea;
      padding-bottom: 8px;
    }}
    .report-header, section {{
      background: #ffffff;
      border: 1px solid #d8e0ea;
      border-radius: 8px;
      margin-bottom: 18px;
      padding: 20px;
      box-shadow: 0 8px 24px rgba(31, 41, 55, 0.06);
    }}
    .meta-grid, .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .meta-card, .summary-card {{
      background: #f8fafc;
      border: 1px solid #e5ebf2;
      border-radius: 6px;
      padding: 12px;
    }}
    .label {{
      display: block;
      color: #64748b;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .value {{
      display: block;
      font-size: 16px;
      font-weight: 700;
      margin-top: 4px;
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 820px;
    }}
    th, td {{
      border-bottom: 1px solid #e5ebf2;
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #eef4fb;
      color: #334155;
      font-size: 13px;
    }}
    tr:last-child td {{
      border-bottom: 0;
    }}
    .inventory {{
      list-style: none;
      margin: 0;
      padding: 0;
      max-width: 360px;
    }}
    .inventory li {{
      align-items: center;
      border-bottom: 1px solid #e5ebf2;
      display: flex;
      justify-content: space-between;
      padding: 10px 0;
    }}
    .inventory li:last-child {{
      border-bottom: 0;
    }}
    .empty {{
      color: #64748b;
      font-style: italic;
      text-align: center;
    }}
  </style>
</head>
<body>
  <main>
    <div class="report-header">
      <h1>NetScout Scan Report</h1>
      <div class="meta-grid">
        <div class="meta-card"><span class="label">Version</span><span class="value">{version}</span></div>
        <div class="meta-card"><span class="label">Detected Network</span><span class="value">{detected_network}</span></div>
        <div class="meta-card"><span class="label">Local IP</span><span class="value">{local_ip}</span></div>
        <div class="meta-card"><span class="label">Gateway</span><span class="value">{gateway}</span></div>
        <div class="meta-card"><span class="label">Export Timestamp</span><span class="value">{html.escape(export_timestamp)}</span></div>
      </div>
    </div>

    <section>
      <h2>Scan Results</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>IP Address</th>
              <th>Hostname</th>
              <th>MAC Address</th>
              <th>Vendor</th>
              <th>Device Type</th>
              <th>Status</th>
              <th>Open Ports</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(result_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section>
      <h2>Device Inventory</h2>
      <ul class="inventory">
{chr(10).join(inventory_items)}
      </ul>
    </section>

    <section>
      <h2>Scan Summary</h2>
      <div class="summary-grid">
        <div class="summary-card"><span class="label">Hosts Scanned</span><span class="value">{html.escape(str(summary.get("hosts_scanned", "0")))}</span></div>
        <div class="summary-card"><span class="label">Live Hosts Found</span><span class="value">{html.escape(str(summary.get("live_hosts_found", "0")))}</span></div>
        <div class="summary-card"><span class="label">Ports Tested</span><span class="value">{html.escape(str(summary.get("ports_tested", "0")))}</span></div>
        <div class="summary-card"><span class="label">Open Ports Found</span><span class="value">{html.escape(str(summary.get("open_ports_found", "0")))}</span></div>
        <div class="summary-card"><span class="label">Elapsed Time</span><span class="value">{html.escape(str(summary.get("elapsed_time", "0.00 seconds")))}</span></div>
      </div>
    </section>
  </main>
</body>
</html>
"""

    with output_path.open("w", encoding="utf-8") as html_file:
        html_file.write(html_text)


def export_scan_results(
    results: list[ScanResult],
    export_format: str,
    output_folder: str,
    report_info: dict[str, Any] | None = None,
) -> list[Path]:
    """Export scan results and return the file paths that were created."""
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    rows = [_result_to_row(result) for result in results]
    export_time = datetime.now()
    file_timestamp = export_time.strftime("%Y%m%d_%H%M%S")
    export_timestamp = _format_export_time(export_time)
    created_files: list[Path] = []

    if export_format in ("csv", "both", "all"):
        csv_path = output_path / f"netscout_scan_{file_timestamp}.csv"
        _write_csv(rows, csv_path)
        created_files.append(csv_path)

    if export_format in ("json", "both", "all"):
        json_path = output_path / f"netscout_scan_{file_timestamp}.json"
        _write_json(rows, json_path)
        created_files.append(json_path)

    if export_format in ("html", "all"):
        html_path = output_path / f"netscout_scan_{file_timestamp}.html"
        _write_html(
            rows=rows,
            output_path=html_path,
            report_info=report_info or {},
            export_timestamp=export_timestamp,
        )
        created_files.append(html_path)

    return created_files
