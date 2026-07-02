"""Local network device helpers."""

from __future__ import annotations

import re
import subprocess


MAC_ADDRESS_PATTERN = re.compile(
    r"(?P<mac>[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5})"
)


def normalize_mac_address(mac_address: str) -> str:
    """Format a MAC address consistently as AA:BB:CC:DD:EE:FF."""
    parts = re.split("[:-]", mac_address.upper())
    return ":".join(parts)


def get_arp_table() -> str:
    """Return the operating system ARP table as text.

    ARP maps local-network IP addresses to MAC addresses. This only works for
    devices on the same local network segment, and usually only after the host
    has been contacted. The ping scan helps populate this cache.
    """
    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""

    return result.stdout


def find_mac_address(ip_address: str, arp_table: str | None = None) -> str:
    """Find the MAC address for an IP address in the local ARP table."""
    table_text = arp_table if arp_table is not None else get_arp_table()

    for line in table_text.splitlines():
        if ip_address not in line:
            continue

        match = MAC_ADDRESS_PATTERN.search(line)
        if match:
            return normalize_mac_address(match.group("mac"))

    return "Unknown"
