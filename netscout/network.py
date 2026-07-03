"""Network detection and configuration utilities."""

from __future__ import annotations

import ipaddress
import re
import socket
import subprocess
from dataclasses import dataclass


@dataclass
class NetworkConfig:
    """Local network configuration information."""

    local_ip: ipaddress.IPv4Address
    subnet_mask: ipaddress.IPv4Address
    cidr_network: ipaddress.IPv4Network
    gateway: ipaddress.IPv4Address | None


def get_local_ip() -> ipaddress.IPv4Address | None:
    """Get the local IPv4 address by connecting to an external endpoint.

    This method doesn't require a real connection; it just uses socket
    to determine which local interface would be used for external traffic.
    """
    try:
        # Connect to a public DNS server (8.8.8.8:53 for Google DNS)
        # The socket doesn't actually send data, just determines routing
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 53))
        local_ip_str = sock.getsockname()[0]
        sock.close()
        return ipaddress.IPv4Address(local_ip_str)
    except (OSError, ValueError):
        return None


def get_subnet_mask_from_ipconfig(
    local_ip: ipaddress.IPv4Address,
) -> ipaddress.IPv4Address | None:
    """Get the subnet mask from Windows ipconfig command.

    Parses the output of 'ipconfig' to find the subnet mask associated with
    the given local IPv4 address.
    """
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    lines = result.stdout.splitlines()
    local_ip_str = str(local_ip)
    in_correct_adapter = False
    found_ip = False

    for i, line in enumerate(lines):
        # Look for lines containing our local IP
        if local_ip_str in line:
            found_ip = True
            in_correct_adapter = True

        # Once we find our IP, look for the subnet mask in nearby lines
        if in_correct_adapter and "Subnet Mask" in line:
            # Extract the subnet mask value
            parts = line.split(":")
            if len(parts) > 1:
                mask_str = parts[1].strip()
                try:
                    return ipaddress.IPv4Address(mask_str)
                except ValueError:
                    return None

        # Stop looking after we've moved to the next adapter
        if found_ip and "Adapter" in line and local_ip_str not in line:
            break

    return None


def get_gateway_from_ipconfig() -> ipaddress.IPv4Address | None:
    """Get the default gateway from Windows ipconfig command.

    Parses the output of 'ipconfig' to find the default gateway.
    """
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    for line in result.stdout.splitlines():
        if "Default Gateway" in line and ":" in line:
            # Extract the gateway IP address
            parts = line.split(":")
            if len(parts) > 1:
                gateway_str = parts[1].strip()
                # Handle multiple gateways separated by commas
                first_gateway = gateway_str.split(",")[0].strip()
                try:
                    return ipaddress.IPv4Address(first_gateway)
                except ValueError:
                    return None

    return None


def mask_to_prefix_length(subnet_mask: ipaddress.IPv4Address) -> int:
    """Convert a subnet mask to CIDR prefix length.

    For example, 255.255.255.0 becomes 24.
    """
    # Convert mask to integer and count leading 1 bits
    mask_int = int(subnet_mask)
    # Count the number of 1 bits from the left
    prefix_length = bin(mask_int).count("1")
    return prefix_length


def detect_network() -> NetworkConfig | None:
    """Automatically detect the local network configuration.

    Returns a NetworkConfig with local IP, subnet mask, CIDR network, and
    gateway information. Returns None if detection fails.
    """
    # Step 1: Get the local IP address
    local_ip = get_local_ip()
    if local_ip is None:
        return None

    # Step 2: Get the subnet mask
    subnet_mask = get_subnet_mask_from_ipconfig(local_ip)
    if subnet_mask is None:
        return None

    # Step 3: Calculate CIDR network
    prefix_length = mask_to_prefix_length(subnet_mask)
    try:
        # Create a network object using the local IP and prefix length
        # strict=False allows using a host address instead of network address
        cidr_network = ipaddress.ip_network(
            f"{local_ip}/{prefix_length}", strict=False
        )
    except ValueError:
        return None

    # Step 4: Get the gateway (optional, may be None)
    gateway = get_gateway_from_ipconfig()

    return NetworkConfig(
        local_ip=local_ip,
        subnet_mask=subnet_mask,
        cidr_network=cidr_network,
        gateway=gateway,
    )
