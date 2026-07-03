"""Command-line interface for NetScout."""

from __future__ import annotations

import argparse
import ipaddress
import shutil
import textwrap
import time
from collections import Counter
from typing import Sequence

from netscout import __version__
from netscout.export import export_scan_results
from netscout.history import (
    compare_with_history,
    find_latest_history_file,
    load_history,
    save_history,
)
from netscout.network import detect_network
from netscout.ports import DEFAULT_PORTS, format_open_ports, get_service_name
from netscout.scanner import ScanResult, scan_subnet


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser used by the application."""
    parser = argparse.ArgumentParser(
        prog="netscout",
        description="NetScout discovers live hosts, identifies devices, and scans TCP ports.",
    )
    parser.add_argument(
        "subnet",
        nargs="?",
        default=None,
        help="IPv4 subnet in CIDR notation, for example: 192.168.1.0/24. If omitted, auto-detects the local network.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Seconds to wait for each ping or TCP response. Default: 1.0",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=64,
        help="Maximum number of concurrent ping requests. Default: 64",
    )
    parser.add_argument(
        "--ports",
        help=(
            "Comma-separated TCP ports to scan. "
            f"Default: {','.join(str(port) for port in DEFAULT_PORTS)}"
        ),
    )
    parser.add_argument(
        "--view",
        choices=("table", "cards"),
        default="table",
        help="Choose scan result display format. Default: table",
    )
    parser.add_argument(
        "--export",
        choices=("csv", "json", "html", "both", "all"),
        help="Save scan results as csv, json, html, both, or all.",
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Folder for exported scan files. Default: results",
    )
    parser.add_argument(
        "--save-history",
        action="store_true",
        help="Save this scan to the local history folder.",
    )
    parser.add_argument(
        "--compare-last",
        action="store_true",
        help="Compare this scan to the most recent previous history file.",
    )
    return parser


def parse_ports(value: str | None) -> list[int]:
    """Parse the optional --ports value into a list of TCP port numbers."""
    if value is None:
        return DEFAULT_PORTS

    ports: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            raise ValueError("port list cannot contain empty values")

        try:
            port = int(item)
        except ValueError as error:
            raise ValueError(f"{item!r} is not a valid port number") from error

        if port < 1 or port > 65535:
            raise ValueError(f"{port} is outside the valid range 1-65535")

        if port not in ports:
            ports.append(port)

    return ports


def print_section_header(title: str) -> None:
    """Print a clean section header for terminal output."""
    print()
    print(title)
    print("-" * len(title))


def _wrap_cell(value: str, width: int) -> list[str]:
    """Wrap a table cell so long text does not wrap messily in the terminal."""
    wrapped_lines = textwrap.wrap(
        value,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return wrapped_lines or [""]


def print_results_table(results: list[ScanResult]) -> None:
    """Print scan results in a simple table.

    The Open Ports column can get long when many ports are open. It is wrapped
    inside the table so the terminal output stays readable.
    """
    headers = (
        "IP Address",
        "Hostname",
        "MAC Address",
        "Vendor",
        "Device Type",
        "Status",
        "Open Ports",
    )
    rows = [
        (
            str(result.ip_address),
            result.hostname,
            result.mac_address,
            result.vendor,
            result.device_type,
            result.status,
            format_open_ports(result.open_ports),
        )
        for result in results
    ]

    terminal_width = shutil.get_terminal_size(fallback=(120, 20)).columns
    separator_width = 3 * (len(headers) - 1)

    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    fixed_width = sum(widths[:-1]) + separator_width

    # Leave the Open Ports column wide enough to be useful, but cap it so a
    # long list wraps neatly instead of spilling across the terminal.
    available_open_ports_width = terminal_width - fixed_width
    widths[-1] = max(20, min(widths[-1], available_open_ports_width))

    header_line = " | ".join(
        f"{header:<{widths[index]}}"
        for index, header in enumerate(headers)
    )
    divider = "-+-".join("-" * width for width in widths)

    print(header_line)
    print(divider)
    for row in rows:
        wrapped_open_ports = _wrap_cell(row[-1], widths[-1])

        for line_index, open_ports_line in enumerate(wrapped_open_ports):
            if line_index == 0:
                display_row = (*row[:-1], open_ports_line)
            else:
                # Continuation lines keep the Open Ports text aligned while the
                # other columns are blank.
                display_row = ("", "", "", "", "", "", open_ports_line)

            print(
                " | ".join(
                    f"{value:<{widths[index]}}"
                    for index, value in enumerate(display_row)
                )
            )


def print_results_cards(results: list[ScanResult]) -> None:
    """Print scan results as compact per-device cards."""
    for index, result in enumerate(results, start=1):
        if index > 1:
            print()

        title = f"Device {index}"
        print(title)
        print("-" * len(title))
        print(f"IP Address: {result.ip_address}")
        print(f"Hostname: {result.hostname}")
        print(f"MAC Address: {result.mac_address}")
        print(f"Vendor: {result.vendor}")
        print(f"Device Type: {result.device_type}")
        print(f"Status: {result.status}")

        if result.open_ports:
            print("Open Ports:")
            for port in result.open_ports:
                print(f"  - {port} ({get_service_name(port)})")
        else:
            print("Open Ports: None")


def _format_ports(ports: object) -> str:
    """Format a plain list of port numbers for history comparison output."""
    if not isinstance(ports, list) or not ports:
        return "None"

    return ", ".join(str(port) for port in ports)


def print_history_comparison(
    comparison: dict[str, list[dict[str, object]]],
) -> None:
    """Print a friendly summary of changes since the last saved scan."""
    if not any(comparison.values()):
        print("No changes found.")
        return

    print("New devices:")
    if comparison["new_devices"]:
        for device in comparison["new_devices"]:
            print(f"  {device['ip_address']} ({device['hostname']})")
    else:
        print("  None")

    print("Missing devices:")
    if comparison["missing_devices"]:
        for device in comparison["missing_devices"]:
            print(f"  {device['ip_address']} ({device['hostname']})")
    else:
        print("  None")

    print("Hostname changes:")
    if comparison["hostname_changes"]:
        for change in comparison["hostname_changes"]:
            print(
                f"  {change['ip_address']}: "
                f"{change['old']} -> {change['new']}"
            )
    else:
        print("  None")

    print("MAC address changes:")
    if comparison["mac_address_changes"]:
        for change in comparison["mac_address_changes"]:
            print(
                f"  {change['ip_address']}: "
                f"{change['old']} -> {change['new']}"
            )
    else:
        print("  None")

    print("Open port changes:")
    if comparison["open_port_changes"]:
        for change in comparison["open_port_changes"]:
            added = _format_ports(change["added"])
            removed = _format_ports(change["removed"])
            print(
                f"  {change['ip_address']}: "
                f"added {added}; removed {removed}"
            )
    else:
        print("  None")


def print_device_inventory(results: list[ScanResult]) -> None:
    """Print a count of devices grouped by detected device type."""
    if not results:
        print("No devices found.")
        return

    inventory = Counter(result.device_type for result in results)

    # Show known device types alphabetically, then Unknown at the end.
    device_types = sorted(
        device_type
        for device_type in inventory
        if device_type != "Unknown"
    )
    if "Unknown" in inventory:
        device_types.append("Unknown")

    for device_type in device_types:
        print(f"{device_type}: {inventory[device_type]}")


def print_scan_summary(
    hosts_scanned: int,
    live_hosts_found: int,
    ports_tested: int,
    open_ports_found: int,
    elapsed_seconds: float,
) -> None:
    """Print a short summary of scan statistics."""
    print(f"Hosts scanned: {hosts_scanned}")
    print(f"Live hosts found: {live_hosts_found}")
    print(f"Ports tested: {ports_tested}")
    print(f"Open ports found: {open_ports_found}")
    print(f"Elapsed time: {elapsed_seconds:.2f} seconds")


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, run the scan, and print the results."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Print NetScout banner
    print(f"NetScout v{__version__.removesuffix('.0')}")
    print_section_header("Network Information")
    local_ip = "Not available"
    gateway = "Not available"

    # If no subnet provided, auto-detect the local network
    if args.subnet is None:
        network_config = detect_network()
        if network_config is None:
            parser.error(
                "could not auto-detect network. Please provide a subnet manually."
            )

        # Print detected network info
        local_ip = str(network_config.local_ip)
        print(f"Local IP: {local_ip}")
        if network_config.gateway:
            gateway = str(network_config.gateway)
            print(f"Gateway: {gateway}")
        else:
            print("Gateway: Not available")
        print(f"Detected Network: {network_config.cidr_network}")

        network = network_config.cidr_network
    else:
        try:
            # strict=False lets users type a host address like 192.168.1.50/24.
            # Python will normalize it to the matching network: 192.168.1.0/24.
            network = ipaddress.ip_network(args.subnet, strict=False)
        except ValueError as error:
            parser.error(f"invalid subnet: {error}")

        print(f"Target Network: {network}")

    if network.version != 4:
        parser.error("only IPv4 subnets are supported")

    if args.timeout <= 0:
        parser.error("--timeout must be greater than 0")

    if args.workers <= 0:
        parser.error("--workers must be greater than 0")

    try:
        ports = parse_ports(args.ports)
    except ValueError as error:
        parser.error(f"invalid --ports value: {error}")

    host_count = network.num_addresses
    if network.prefixlen < 31:
        # Normal IPv4 networks reserve one address for the network itself and
        # one address for broadcast, so those are not useful host targets.
        host_count -= 2

    print_section_header("Scan Results")
    print(f"Scanning {host_count} hosts on {network}...\n")

    # Measure only the actual scan work, not argument parsing or printing.
    scan_started_at = time.perf_counter()
    results = scan_subnet(
        network=network,
        ports=ports,
        timeout=args.timeout,
        max_workers=args.workers,
    )
    elapsed_seconds = time.perf_counter() - scan_started_at

    if results and args.view == "table":
        print_results_table(results)
    elif results and args.view == "cards":
        print_results_cards(results)
    else:
        print("No live hosts found.")

    print_section_header("Device Inventory")
    print_device_inventory(results)

    open_ports_found = sum(len(result.open_ports) for result in results)
    print_section_header("Scan Summary")
    print_scan_summary(
        hosts_scanned=host_count,
        live_hosts_found=len(results),
        ports_tested=len(ports),
        open_ports_found=open_ports_found,
        elapsed_seconds=elapsed_seconds,
    )

    print(f"\nScan complete. Found {len(results)} live host(s).")

    if args.compare_last:
        print_section_header("History Comparison")
        latest_history = find_latest_history_file()
        if latest_history is None:
            print("No previous history file found.")
        else:
            previous_results = load_history(latest_history)
            comparison = compare_with_history(results, previous_results)
            print(f"Compared with: {latest_history}")
            print_history_comparison(comparison)

    if args.save_history:
        history_path = save_history(results)
        print(f"Saved history: {history_path}")

    if args.export:
        print_section_header("Export Results")
        report_info = {
            "version": f"NetScout v{__version__.removesuffix('.0')}",
            "detected_network": str(network),
            "local_ip": local_ip,
            "gateway": gateway,
            "summary": {
                "hosts_scanned": host_count,
                "live_hosts_found": len(results),
                "ports_tested": len(ports),
                "open_ports_found": open_ports_found,
                "elapsed_time": f"{elapsed_seconds:.2f} seconds",
            },
        }
        created_files = export_scan_results(
            results=results,
            export_format=args.export,
            output_folder=args.output,
            report_info=report_info,
        )

        for path in created_files:
            # The suffix tells us which friendly label to print.
            if path.suffix.lower() == ".csv":
                print(f"Exported CSV: {path}")
            elif path.suffix.lower() == ".json":
                print(f"Exported JSON: {path}")
            elif path.suffix.lower() == ".html":
                print(f"Exported HTML: {path}")

    return 0
