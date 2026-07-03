# NetScout

A beginner-friendly Python network scanner that discovers live hosts on an IPv4 subnet using concurrent ping requests.

Version 3.3 adds scan history and comparison support, so you can save snapshots and see what changed between scans. The code remains modular, commented, and built only with the Python standard library.

## Features

- **Auto-detect local network**: Run without arguments to automatically detect your IPv4 network, gateway, and CIDR
- Scan an IPv4 subnet in CIDR notation, such as `192.168.1.0/24`
- Ping many hosts concurrently for faster discovery
- Display every live host found in a clean table
- Look up the hostname for each live host
- Show `Unknown` when a live host has no hostname
- Scan common TCP ports on each live host
- Display service names beside open ports, such as `445 (SMB)`
- Show `None` when a live host has no open ports
- Customize scanned ports with `--ports`
- Export scan results to CSV, JSON, or both with `--export`
- Choose the export folder with `--output`
- Save scan history snapshots with `--save-history`
- Compare the current scan to the last saved history with `--compare-last`
- Detect MAC addresses for live hosts on the local network
- Identify common hardware vendors from the MAC address OUI
- Keep command-line parsing, network detection, ping logic, and scanning logic in separate modules
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
    |-- export.py
    |-- history.py
    |-- network.py
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

### Auto-detect your local network

Run the scanner without a subnet to automatically detect your local IPv4 network:

```powershell
python -m netscout
```

This will:
- Detect your local IPv4 address
- Query the system for your subnet mask
- Calculate the CIDR network (e.g., 192.168.1.0/24)
- Find your default gateway if available
- Scan the entire network

Example output:

```
NetScout v3.3
Local IP: 192.168.1.100
Gateway: 192.168.1.1
Detected Network: 192.168.1.0/24

Scanning 254 hosts on 192.168.1.0/24...
```

### Manual subnet specification

Provide a subnet in CIDR notation:

```powershell
python -m netscout 192.168.1.0/24
```

This will:

```
NetScout v3.3

Scanning 254 hosts on 192.168.1.0/24...
```

### Custom timeout and concurrency

Use custom timeout and concurrency settings:

```powershell
python -m netscout --timeout 1.0 --workers 100
```

Or with a manual subnet:

```powershell
python -m netscout 192.168.1.0/24 --timeout 1.0 --workers 100
```

### Scan custom TCP ports

Scan custom TCP ports on all discovered hosts:

```powershell
python -m netscout --ports 22,80,443,445,3389
```

Or with a manual subnet:

```powershell
python -m netscout 192.168.232.0/24 --ports 22,80,443,445,3389
```

By default, the scanner checks these common ports:

```text
22, 53, 80, 135, 139, 443, 445, 3389, 8080
```

### Export scan results

Save scan results to the default `results` folder as CSV:

```powershell
python -m netscout --export csv
```

Save scan results as JSON:

```powershell
python -m netscout --export json
```

Save both CSV and JSON files:

```powershell
python -m netscout --export both
```

Use a manual subnet, custom ports, both export formats, and an output folder:

```powershell
python -m netscout 192.168.1.0/24 --ports 22,80,443,445 --export both --output results
```

Exported files use timestamped names:

```text
netscout_scan_YYYYMMDD_HHMMSS.csv
netscout_scan_YYYYMMDD_HHMMSS.json
```

Each export includes `ip_address`, `hostname`, `mac_address`, `vendor`, `status`, and `open_ports`.

After an export, NetScout prints the saved file path:

```text
Exported CSV: results\netscout_scan_20260703_102620.csv
Exported JSON: results\netscout_scan_20260703_102620.json
```

### Save and compare scan history

Save the current scan to the default `history` folder:

```powershell
python -m netscout --save-history
```

Compare the current scan to the most recent previous history file:

```powershell
python -m netscout --compare-last
```

Compare the current scan first, then save it as the newest history snapshot:

```powershell
python -m netscout --save-history --compare-last
```

History files use timestamped names:

```text
netscout_history_YYYYMMDD_HHMMSS.json
```

The comparison report shows new devices, missing devices, hostname changes, MAC address changes, and open port changes.

## Example Output

With auto-detection (no subnet provided):

```text
NetScout v3.3
Local IP: 192.168.1.100
Gateway: 192.168.1.1
Detected Network: 192.168.1.0/24

Scanning 254 hosts on 192.168.1.0/24...

IP Address   | Hostname     | MAC Address       | Vendor  | Status | Open Ports
-------------+--------------+-------------------+---------+--------+--------------------------
192.168.1.1  | router.local | A0:F3:C1:12:34:56 | TP-Link | Live   | 53 (DNS), 80 (HTTP)
192.168.1.25 | laptop.local | D0:67:E5:AA:BB:CC | Dell    | Live   | 445 (SMB), 3389 (RDP)
192.168.1.42 | Unknown      | Unknown           | Unknown | Live   | None

Scan complete. Found 3 live host(s).
```

With manual subnet:

```text
NetScout v3.3

Scanning 254 hosts on 192.168.1.0/24...

IP Address   | Hostname     | MAC Address       | Vendor  | Status | Open Ports
-------------+--------------+-------------------+---------+--------+--------------------------
192.168.1.1  | router.local | A0:F3:C1:12:34:56 | TP-Link | Live   | 53 (DNS), 80 (HTTP)
192.168.1.25 | laptop.local | D0:67:E5:AA:BB:CC | Dell    | Live   | 445 (SMB), 3389 (RDP)
192.168.1.42 | Unknown      | Unknown           | Unknown | Live   | None

Scan complete. Found 3 live host(s).
```

## How It Works

1. `cli.py` reads the subnet from command-line arguments.
2. If no subnet is provided, `network.py` auto-detects the local IPv4 network.
3. `network.py` uses system commands (`ipconfig` on Windows) to find:
   - Your local IPv4 address (via socket routing)
   - Your subnet mask (from ipconfig output)
   - Your default gateway (from ipconfig output)
   - Calculates CIDR notation from the subnet mask
4. `scanner.py` expands the subnet into individual host addresses.
5. `scanner.py` uses a thread pool to ping many hosts at the same time.
6. `ping.py` runs the correct system `ping` command for your operating system.
7. For each live host, `scanner.py` tries a reverse DNS lookup to find a hostname.
8. `device.py` reads the local ARP table to find the host MAC address when possible.
9. `vendor.py` uses the MAC address OUI to identify common hardware vendors.
10. `ports.py` checks common TCP ports, or the ports provided with `--ports`.
11. The CLI prints each live host in a table with IP address, hostname, MAC address, vendor, status, and open ports.
12. If `--export` is used, `export.py` saves the same scan fields to CSV, JSON, or both.
13. If `--save-history` is used, `history.py` saves the scan to a timestamped JSON file.
14. If `--compare-last` is used, `history.py` compares the current scan with the newest previous history file.

## Device Intelligence Notes

MAC address detection depends on the local ARP table. This works best for devices on your own local network after they have responded to ping. Devices outside your local network, devices blocked by firewall rules, or hosts that do not appear in ARP will show `Unknown`.

Vendor detection uses a small built-in OUI table for common vendors including Dell, HP, Cisco, Intel, ASUS, TP-Link, Ubiquiti, Synology, Apple, Microsoft, VMware, Raspberry Pi, and Netgear. The table lives in `vendor.py` so it can be expanded later.

## Safety Note

Only scan networks you own or have permission to test. Even a basic ping scan can be unwanted traffic on networks you do not control.
