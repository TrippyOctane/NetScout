# NetScout

A beginner-friendly Python network scanner that discovers live hosts on an IPv4 subnet using concurrent ping requests.

Version 3.0 adds device intelligence while keeping the code modular, commented, and built only with the Python standard library.

## Features

- Scan an IPv4 subnet in CIDR notation, such as `192.168.1.0/24`
- Ping many hosts concurrently for faster discovery
- Display every live host found in a clean table
- Look up the hostname for each live host
- Show `Unknown` when a live host has no hostname
- Scan common TCP ports on each live host
- Display service names beside open ports, such as `445 (SMB)`
- Show `None` when a live host has no open ports
- Customize scanned ports with `--ports`
- Detect MAC addresses for live hosts on the local network
- Identify common hardware vendors from the MAC address OUI
- Keep command-line parsing, ping logic, and scanning logic in separate modules
- Use clear comments and type hints for learning

## Project Structure

```text
netscout/
|-- README.md
|-- requirements.txt
|-- .gitignore
`-- netscout/
    |-- __init__.py
    |-- __main__.py
    |-- cli.py
    |-- device.py
    |-- ping.py
    |-- ports.py
    |-- scanner.py
    `-- vendor.py
```

## Requirements

- Python 3.10 or newer
- The system `ping` command

No third-party Python packages are required.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install requirements:

```powershell
python -m pip install -r requirements.txt
```

## Usage

Run the scanner as a module:

```powershell
python -m netscout 192.168.1.0/24
```

Use custom timeout and concurrency settings:

```powershell
python -m netscout 192.168.1.0/24 --timeout 1.0 --workers 100
```

Scan custom TCP ports:

```powershell
python -m netscout 192.168.232.0/24 --ports 22,80,443,3389
```

By default, the scanner checks these common ports:

```text
22, 53, 80, 135, 139, 443, 445, 3389, 8080
```

## Example Output

```text
Scanning 254 hosts on 192.168.1.0/24...

Live hosts:
IP Address   | Hostname     | MAC Address       | Vendor  | Status | Open Ports
-------------+--------------+-------------------+---------+--------+--------------------------
192.168.1.1  | router.local | A0:F3:C1:12:34:56 | TP-Link | Live   | 53 (DNS), 80 (HTTP)
192.168.1.25 | laptop.local | D0:67:E5:AA:BB:CC | Dell    | Live   | 445 (SMB), 3389 (RDP)
192.168.1.42 | Unknown      | Unknown           | Unknown | Live   | None

Scan complete. Found 3 live host(s).
```

## How It Works

1. `cli.py` reads the subnet and options from the command line.
2. `scanner.py` expands the subnet into individual host addresses.
3. `scanner.py` uses a thread pool to ping many hosts at the same time.
4. `ping.py` runs the correct system `ping` command for your operating system.
5. For each live host, `scanner.py` tries a reverse DNS lookup to find a hostname.
6. `device.py` reads the local ARP table to find the host MAC address when possible.
7. `vendor.py` uses the MAC address OUI to identify common hardware vendors.
8. `ports.py` checks common TCP ports, or the ports provided with `--ports`.
9. The CLI prints each live host in a table with IP address, hostname, MAC address, vendor, status, and open ports.

## Device Intelligence Notes

MAC address detection depends on the local ARP table. This works best for devices on your own local network after they have responded to ping. Devices outside your local network, devices blocked by firewall rules, or hosts that do not appear in ARP will show `Unknown`.

Vendor detection uses a small built-in OUI table for common vendors including Dell, HP, Cisco, Intel, ASUS, TP-Link, Ubiquiti, Synology, Apple, Microsoft, VMware, Raspberry Pi, and Netgear. The table lives in `vendor.py` so it can be expanded later.

## Safety Note

Only scan networks you own or have permission to test. Even a basic ping scan can be unwanted traffic on networks you do not control.

