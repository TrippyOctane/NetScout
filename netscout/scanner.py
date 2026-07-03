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
    device_type: str
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


def infer_device_type(hostname: str, vendor: str, open_ports: list[int]) -> str:
    """Guess a simple device type from hostname, vendor, and open ports.

    These rules are intentionally basic and easy to read. They are not perfect,
    but they give beginners a helpful first guess.

    >>> infer_device_type("DESKTOP-123", "Dell", [])
    'Windows PC'
    >>> infer_device_type("Pixel-9-Pro", "Google", [])
    'Phone'
    >>> infer_device_type("front-camera", "Unknown", [])
    'Camera'
    >>> infer_device_type("Unknown", "Unknown", [9100])
    'Printer'
    """
    hostname_text = hostname.lower()
    vendor_text = vendor.lower()
    open_port_set = set(open_ports)

    if (
        "desktop" in hostname_text
        or "pc" in hostname_text
        or vendor_text in ("dell", "hp", "microsoft")
        or open_port_set & {135, 139, 445}
    ):
        return "Windows PC"

    if (
        "iphone" in hostname_text
        or "pixel" in hostname_text
        or "android" in hostname_text
        or vendor_text in ("apple", "google", "samsung")
    ):
        return "Phone"

    if (
        "ring" in hostname_text
        or "cam" in hostname_text
        or "camera" in hostname_text
        or vendor_text == "ring"
    ):
        return "Camera"

    if (
        "aqara" in hostname_text
        or "hub" in hostname_text
        or vendor_text == "aqara"
    ):
        return "Smart Hub"

    if (
        "router" in hostname_text
        or "gateway" in hostname_text
        or vendor_text in ("tp-link", "asus", "netgear", "ubiquiti")
        or open_port_set & {53, 80, 443}
    ):
        return "Router"

    if "printer" in hostname_text or 9100 in open_port_set:
        return "Printer"

    return "Unknown"


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
                hostname = lookup_hostname(host)
                vendor = lookup_vendor(mac_address)
                open_ports = scan_ports(
                    address=str(host),
                    ports=ports_to_scan,
                    timeout=timeout,
                )

                results.append(
                    ScanResult(
                        ip_address=host,
                        hostname=hostname,
                        mac_address=mac_address,
                        vendor=vendor,
                        device_type=infer_device_type(
                            hostname=hostname,
                            vendor=vendor,
                            open_ports=open_ports,
                        ),
                        open_ports=open_ports,
                    )
                )

    return sorted(results, key=lambda result: result.ip_address)
