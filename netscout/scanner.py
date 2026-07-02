"""Concurrent IPv4 subnet scanning logic."""

from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from netscout.device import find_mac_address, get_arp_table
from netscout.ping import ping_host
from netscout.ports import DEFAULT_PORTS, scan_ports
from netscout.vendor import lookup_vendor


@dataclass(frozen=True)
class ScanResult:
    """Information we know about one live host."""

    ip_address: ipaddress.IPv4Address
    hostname: str
    mac_address: str
    vendor: str
    open_ports: list[int]
    status: str = "Live"


def lookup_hostname(address: ipaddress.IPv4Address) -> str:
    """Return the hostname for an IP address, or Unknown if none is found.

    Reverse DNS records are optional, so many live devices will not have a
    hostname. That is normal, and the scanner handles it gracefully.
    """
    try:
        hostname, _, _ = socket.gethostbyaddr(str(address))
    except OSError:
        return "Unknown"

    return hostname or "Unknown"


def scan_subnet(
    network: ipaddress.IPv4Network,
    ports: list[int] | None = None,
    timeout: float = 1.0,
    max_workers: int = 64,
) -> list[ScanResult]:
    """Scan an IPv4 network and return results for hosts that respond to ping.

    Ping waits on network I/O, so threads are a good fit here. While one ping
    waits for a response, other pings can run at the same time.
    """
    results: list[ScanResult] = []
    ports_to_scan = ports or DEFAULT_PORTS

    # network.hosts() gives us usable host addresses. For a normal /24 network,
    # it skips the network address (.0) and broadcast address (.255).
    hosts = list(network.hosts())

    # Do not create more worker threads than we have hosts to scan.
    worker_count = min(max_workers, len(hosts)) or 1

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        # Submit all ping jobs up front and remember which host belongs to each
        # Future. A Future represents work that is running or will run soon.
        future_to_host = {
            executor.submit(ping_host, str(host), timeout): host
            for host in hosts
        }

        # as_completed yields futures as soon as they finish, regardless of the
        # order they were submitted in.
        for future in as_completed(future_to_host):
            host = future_to_host[future]
            if future.result():
                # Ping usually populates the ARP cache for local hosts. We read
                # the table after a host responds so MAC lookup has a chance.
                arp_table = get_arp_table()
                mac_address = find_mac_address(str(host), arp_table)

                results.append(
                    ScanResult(
                        ip_address=host,
                        hostname=lookup_hostname(host),
                        mac_address=mac_address,
                        vendor=lookup_vendor(mac_address),
                        open_ports=scan_ports(
                            address=str(host),
                            ports=ports_to_scan,
                            timeout=timeout,
                        ),
                    )
                )

    return sorted(results, key=lambda result: result.ip_address)
