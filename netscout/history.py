"""Save NetScout scan history and compare scans over time."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from netscout.scanner import ScanResult


HISTORY_FOLDER = "history"
HISTORY_PREFIX = "netscout_history_"
HISTORY_SUFFIX = ".json"


def _timestamp() -> str:
    """Return a timestamp that is safe to use in filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _result_to_row(result: ScanResult) -> dict[str, object]:
    """Convert one ScanResult into simple values for a history file."""
    return {
        "ip_address": str(result.ip_address),
        "hostname": result.hostname,
        "mac_address": result.mac_address,
        "vendor": result.vendor,
        "status": result.status,
        "open_ports": result.open_ports,
    }


def save_history(
    results: list[ScanResult],
    history_folder: str = HISTORY_FOLDER,
) -> Path:
    """Save the current scan results to a timestamped history JSON file."""
    folder_path = Path(history_folder)
    folder_path.mkdir(parents=True, exist_ok=True)

    history_path = folder_path / f"{HISTORY_PREFIX}{_timestamp()}{HISTORY_SUFFIX}"
    history_data = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "results": [_result_to_row(result) for result in results],
    }

    with history_path.open("w", encoding="utf-8") as history_file:
        json.dump(history_data, history_file, indent=2)
        history_file.write("\n")

    return history_path


def find_latest_history_file(
    history_folder: str = HISTORY_FOLDER,
) -> Path | None:
    """Return the newest history file, or None if no history exists yet."""
    folder_path = Path(history_folder)
    if not folder_path.exists():
        return None

    history_files = sorted(
        folder_path.glob(f"{HISTORY_PREFIX}*{HISTORY_SUFFIX}")
    )
    if not history_files:
        return None

    return history_files[-1]


def load_history(history_path: Path) -> list[dict[str, Any]]:
    """Load scan results from a history JSON file."""
    with history_path.open("r", encoding="utf-8") as history_file:
        history_data = json.load(history_file)

    # History files store results inside a small metadata wrapper. This
    # fallback also accepts a plain list in case a beginner edits a file by hand.
    if isinstance(history_data, dict):
        results = history_data.get("results", [])
    else:
        results = history_data

    if not isinstance(results, list):
        return []

    return [
        result
        for result in results
        if isinstance(result, dict) and "ip_address" in result
    ]


def _rows_by_ip(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index exported-style rows by IP address for easy comparison."""
    return {
        str(row["ip_address"]): row
        for row in rows
    }


def _ports_from_row(row: dict[str, Any]) -> set[int]:
    """Return open ports from a history row as a set of integers."""
    ports = row.get("open_ports", [])
    if not isinstance(ports, list):
        return set()

    return {
        port
        for port in ports
        if isinstance(port, int)
    }


def compare_with_history(
    current_results: list[ScanResult],
    previous_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Compare the current scan with a previous history file."""
    current_rows = [_result_to_row(result) for result in current_results]
    current_by_ip = _rows_by_ip(current_rows)
    previous_by_ip = _rows_by_ip(previous_rows)

    current_ips = set(current_by_ip)
    previous_ips = set(previous_by_ip)
    matching_ips = sorted(current_ips & previous_ips)

    comparison: dict[str, list[dict[str, Any]]] = {
        "new_devices": [],
        "missing_devices": [],
        "hostname_changes": [],
        "mac_address_changes": [],
        "open_port_changes": [],
    }

    for ip_address in sorted(current_ips - previous_ips):
        comparison["new_devices"].append(current_by_ip[ip_address])

    for ip_address in sorted(previous_ips - current_ips):
        comparison["missing_devices"].append(previous_by_ip[ip_address])

    for ip_address in matching_ips:
        current = current_by_ip[ip_address]
        previous = previous_by_ip[ip_address]

        if current.get("hostname") != previous.get("hostname"):
            comparison["hostname_changes"].append(
                {
                    "ip_address": ip_address,
                    "old": previous.get("hostname", "Unknown"),
                    "new": current.get("hostname", "Unknown"),
                }
            )

        if current.get("mac_address") != previous.get("mac_address"):
            comparison["mac_address_changes"].append(
                {
                    "ip_address": ip_address,
                    "old": previous.get("mac_address", "Unknown"),
                    "new": current.get("mac_address", "Unknown"),
                }
            )

        current_ports = _ports_from_row(current)
        previous_ports = _ports_from_row(previous)
        if current_ports != previous_ports:
            comparison["open_port_changes"].append(
                {
                    "ip_address": ip_address,
                    "added": sorted(current_ports - previous_ports),
                    "removed": sorted(previous_ports - current_ports),
                }
            )

    return comparison
