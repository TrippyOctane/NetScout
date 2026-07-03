"""Command-line interface for NetScout."""

from __future__ import annotations

import argparse
import ipaddress
from typing import Sequence

from netscout import __version__
from netscout.export import export_scan_results
from netscout.network import detect_network
from netscout.ports import DEFAULT_PORTS, format_open_ports
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
        "--export",
        choices=("csv", "json", "both"),
        help="Save scan results as csv, json, or both.",
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Folder for exported scan files. Default: results",
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


def print_results_table(results: list[ScanResult]) -> None:
    """Print scan results in a simple table.

    The table widths are calculated from the data, so longer hostnames and port
    lists still line up without requiring a third-party formatting package.
    """
    headers = (
        "IP Address",
        "Hostname",
        "MAC Address",
        "Vendor",
        "Status",
        "Open Ports",
    )
    rows = [
        (
            str(result.ip_address),
            result.hostname,
            result.mac_address,
            result.vendor,
            result.status,
            format_open_ports(result.open_ports),
        )
        for result in results
    ]

    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]

    header_line = " | ".join(
        f"{header:<{widths[index]}}"
        for index, header in enumerate(headers)
    )
    divider = "-+-".join("-" * width for width in widths)

    print(header_line)
    print(divider)
    for row in rows:
        print(
            " | ".join(
                f"{value:<{widths[index]}}"
                for index, value in enumerate(row)
            )
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, run the scan, and print the results."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Print NetScout banner
    print(f"NetScout v{__version__.removesuffix('.0')}")

    # If no subnet provided, auto-detect the local network
    if args.subnet is None:
        network_config = detect_network()
        if network_config is None:
            parser.error(
                "could not auto-detect network. Please provide a subnet manually."
            )

        # Print detected network info
        print(f"Local IP: {network_config.local_ip}")
        if network_config.gateway:
            print(f"Gateway: {network_config.gateway}")
        else:
            print("Gateway: Not available")
        print(f"Detected Network: {network_config.cidr_network}\n")

        network = network_config.cidr_network
    else:
        try:
            # strict=False lets users type a host address like 192.168.1.50/24.
            # Python will normalize it to the matching network: 192.168.1.0/24.
            network = ipaddress.ip_network(args.subnet, strict=False)
        except ValueError as error:
            parser.error(f"invalid subnet: {error}")

        print()  # Blank line for formatting

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

    print(f"Scanning {host_count} hosts on {network}...\n")

    results = scan_subnet(
        network=network,
        ports=ports,
        timeout=args.timeout,
        max_workers=args.workers,
    )

    if results:
        print_results_table(results)
    else:
        print("No live hosts found.")

    print(f"\nScan complete. Found {len(results)} live host(s).")

    if args.export:
        created_files = export_scan_results(
            results=results,
            export_format=args.export,
            output_folder=args.output,
        )

        for path in created_files:
            # The suffix tells us which friendly label to print.
            if path.suffix.lower() == ".csv":
                print(f"Exported CSV: {path}")
            elif path.suffix.lower() == ".json":
                print(f"Exported JSON: {path}")

    return 0
