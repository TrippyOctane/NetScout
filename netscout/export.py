"""Export NetScout scan results to CSV and JSON files."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from netscout.scanner import ScanResult


EXPORT_FIELDS = (
    "ip_address",
    "hostname",
    "mac_address",
    "vendor",
    "status",
    "open_ports",
)


def _timestamp() -> str:
    """Return a timestamp that is safe to use in filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _result_to_row(result: ScanResult) -> dict[str, object]:
    """Convert one ScanResult into simple values for export files."""
    return {
        "ip_address": str(result.ip_address),
        "hostname": result.hostname,
        "mac_address": result.mac_address,
        "vendor": result.vendor,
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


def export_scan_results(
    results: list[ScanResult],
    export_format: str,
    output_folder: str,
) -> list[Path]:
    """Export scan results and return the file paths that were created."""
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    rows = [_result_to_row(result) for result in results]
    file_timestamp = _timestamp()
    created_files: list[Path] = []

    if export_format in ("csv", "both"):
        csv_path = output_path / f"netscout_scan_{file_timestamp}.csv"
        _write_csv(rows, csv_path)
        created_files.append(csv_path)

    if export_format in ("json", "both"):
        json_path = output_path / f"netscout_scan_{file_timestamp}.json"
        _write_json(rows, json_path)
        created_files.append(json_path)

    return created_files
