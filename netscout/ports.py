"""TCP port scanning helpers."""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed


# These are common ports beginners are likely to recognize:
# 22 SSH, 53 DNS, 80 HTTP, 135/139/445 Windows networking,
# 443 HTTPS, 3389 Remote Desktop, and 8080 alternate HTTP.
DEFAULT_PORTS = [22, 53, 80, 135, 139, 443, 445, 3389, 8080]


# Friendly service names for common ports. This dictionary is separate from the
# scanning logic so it can be expanded later without changing how sockets work.
SERVICE_NAMES = {
    22: "SSH",
    53: "DNS",
    80: "HTTP",
    135: "MSRPC",
    139: "NetBIOS",
    443: "HTTPS",
    445: "SMB",
    3389: "RDP",
    8080: "HTTP-Alt",
}


def get_service_name(port: int) -> str:
    """Return a friendly service name for a TCP port."""
    return SERVICE_NAMES.get(port, "Unknown")


def format_open_ports(open_ports: list[int]) -> str:
    """Format open ports for display in the results table."""
    if not open_ports:
        return "None"

    return ", ".join(
        f"{port} ({get_service_name(port)})"
        for port in open_ports
    )


def is_port_open(address: str, port: int, timeout: float = 1.0) -> bool:
    """Return True if a TCP connection to an address and port succeeds."""
    try:
        # create_connection handles the socket setup and timeout for us.
        with socket.create_connection((address, port), timeout=timeout):
            return True
    except OSError:
        # Connection refused, timeout, and unreachable hosts all mean the port
        # should not be reported as open.
        return False


def scan_ports(
    address: str,
    ports: list[int],
    timeout: float = 1.0,
    max_workers: int = 32,
) -> list[int]:
    """Scan a list of TCP ports and return the ports that are open.

    Port checks also wait on network I/O, so a small thread pool keeps the scan
    responsive without making the code hard to understand.
    """
    open_ports: list[int] = []
    worker_count = min(max_workers, len(ports)) or 1

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_port = {
            executor.submit(is_port_open, address, port, timeout): port
            for port in ports
        }

        for future in as_completed(future_to_port):
            port = future_to_port[future]
            if future.result():
                open_ports.append(port)

    return sorted(open_ports)
