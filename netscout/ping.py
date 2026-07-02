"""Utilities for sending one ping request to one IPv4 address."""

from __future__ import annotations

import platform
import subprocess


def build_ping_command(address: str, timeout: float) -> list[str]:
    """Build the correct ping command for the current operating system.

    The `ping` command is not exactly the same everywhere:
    - Windows uses `-n` for count and `-w` for timeout in milliseconds.
    - macOS uses `-c` for count and `-W` for timeout in milliseconds.
    - Linux commonly uses `-c` for count and `-W` for timeout in seconds.
    """
    system_name = platform.system().lower()

    if system_name == "windows":
        timeout_ms = max(1, int(timeout * 1000))
        return ["ping", "-n", "1", "-w", str(timeout_ms), address]

    if system_name == "darwin":
        timeout_ms = max(1, int(timeout * 1000))
        return ["ping", "-c", "1", "-W", str(timeout_ms), address]

    timeout_seconds = max(1, int(round(timeout)))
    return ["ping", "-c", "1", "-W", str(timeout_seconds), address]


def ping_host(address: str, timeout: float = 1.0) -> bool:
    """Return True if an address responds to one ping request."""
    command = build_ping_command(address, timeout)

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1,
            check=False,
        )
    except (subprocess.SubprocessError, OSError):
        # SubprocessError covers timeouts and ping execution failures.
        # OSError covers cases where the operating system cannot find `ping`.
        return False

    return result.returncode == 0
