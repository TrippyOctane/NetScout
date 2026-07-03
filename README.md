# NetScout

A beginner-friendly Python network scanner that discovers live hosts on an IPv4 subnet using concurrent ping requests.

Version 4.1 adds `--open-report`, which can automatically open generated HTML reports in your default web browser. The code remains modular, commented, and built only with the Python standard library.

## Features

- **Auto-detect local network**: Run without arguments to automatically detect your IPv4 network, gateway, and CIDR
- Scan an IPv4 subnet in CIDR notation, such as `192.168.1.0/24`
- Ping many hosts concurrently for faster discovery
- Display every live host found in a clean table
- Switch between table and card-style scan results with `--view`
- Wrap long open-port lists cleanly inside the results table
- Display scan statistics and elapsed scan time after each run
- Look up the hostname for each live host
- Show `Unknown` when a live host has no hostname
- Scan common TCP ports on each live host
- Display service names beside open ports, such as `445 (SMB)`
- Show `None` when a live host has no open ports
- Customize scanned ports with `--ports`
- Export scan results to CSV, JSON, or both with `--export`
- Export a clean standalone HTML report with `--export html` or `--export all`
- Open generated HTML reports automatically with `--open-report`
- Choose the export folder with `--output`
- Save scan history snapshots with `--save-history`
- Compare the current scan to the last saved history with `--compare-last`
- Detect MAC addresses for live hosts on the local network
- Identify common hardware vendors from the first 3 bytes of each MAC address
- Infer a basic device type from hostname, vendor, and open ports
- Count discovered devices by device type in a Device Inventory summary
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
NetScout v4.1

Network Information
-------------------
Local IP: 192.168.1.100
Gateway: 192.168.1.1
Detected Network: 192.168.1.0/24

Scan Results
------------
Scanning 254 hosts on 192.168.1.0/24...
```

### Manual subnet specification

Provide a subnet in CIDR notation:

```powershell
python -m netscout 192.168.1.0/24
```

This will:

```
NetScout v4.1

Network Information
-------------------
Target Network: 192.168.1.0/24

Scan Results
------------
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

### Choose a result view

The default view is the table view:

```powershell
python -m netscout --view table
```

Use card view for compact per-device output:

```powershell
python -m netscout --view cards
```

Card view also works with manual subnets and custom ports:

```powershell
python -m netscout 192.168.1.0/24 --ports 22,80,443,445 --view cards
```

The `--view` option only changes terminal output. Exports and history files keep the same fields.

### Export scan results

Save scan results to the default `results` folder as CSV:

```powershell
python -m netscout --export csv
```

Save scan results as JSON:

```powershell
python -m netscout --export json
```

Save an HTML report:

```powershell
python -m netscout --export html
```

Save an HTML report and open it in your default browser:

```powershell
python -m netscout --export html --open-report
```

Save both CSV and JSON files:

```powershell
python -m netscout --export both
```

Save CSV, JSON, and HTML files:

```powershell
python -m netscout --export all
```

Save all formats and open the HTML report:

```powershell
python -m netscout --export all --open-report
```

Use a manual subnet, custom ports, both export formats, and an output folder:

```powershell
python -m netscout 192.168.1.0/24 --ports 22,80,443,445 --export both --output results
```

Use a manual subnet, custom ports, all export formats, and an output folder:

```powershell
python -m netscout 192.168.1.0/24 --ports 22,80,443,445 --export all --output results
```

`--export both` exports CSV and JSON only. Use `--export all` to include HTML.

If `--open-report` is used without `--export html` or `--export all`, NetScout prints:

```text
No HTML report was generated. Use --export html or --export all with --open-report.
```

Exported files use timestamped names:

```text
netscout_scan_YYYYMMDD_HHMMSS.csv
netscout_scan_YYYYMMDD_HHMMSS.json
netscout_scan_YYYYMMDD_HHMMSS.html
```

Each export includes `ip_address`, `hostname`, `mac_address`, `vendor`, `device_type`, `status`, and `open_ports`.

HTML reports also include the NetScout version, detected network, local IP, gateway, device inventory, scan summary, and export timestamp.

After an export, NetScout prints the saved file path:

```text
Export Results
--------------
Exported CSV: results\netscout_scan_20260703_102620.csv
Exported JSON: results\netscout_scan_20260703_102620.json
Exported HTML: results\netscout_scan_20260703_102620.html
Opened HTML report: results\netscout_scan_20260703_102620.html
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

```text
History Comparison
------------------
Compared with: history\netscout_history_20260703_102600.json
No changes found.
```

### Scan summary

After the results table, NetScout prints a device inventory and scan summary:

```text
Device Inventory
----------------
Router: 1
Windows PC: 1
Unknown: 1
```

```text
Scan Summary
------------
Hosts scanned: 254
Live hosts found: 3
Ports tested: 9
Open ports found: 4
Elapsed time: 12.34 seconds
```

## Example Output

With auto-detection (no subnet provided):

```text
NetScout v4.1

Network Information
-------------------
Local IP: 192.168.1.100
Gateway: 192.168.1.1
Detected Network: 192.168.1.0/24

Scan Results
------------
Scanning 254 hosts on 192.168.1.0/24...

IP Address   | Hostname     | MAC Address       | Vendor  | Device Type | Status | Open Ports
-------------+--------------+-------------------+---------+-------------+--------+--------------------------
192.168.1.1  | router.local | A0:F3:C1:12:34:56 | TP-Link | Router      | Live   | 53 (DNS), 80 (HTTP)
192.168.1.25 | laptop.local | D0:67:E5:AA:BB:CC | Dell    | Windows PC  | Live   | 445 (SMB), 3389 (RDP)
192.168.1.42 | Unknown      | Unknown           | Unknown | Unknown     | Live   | None

Device Inventory
----------------
Router: 1
Windows PC: 1
Unknown: 1

Scan Summary
------------
Hosts scanned: 254
Live hosts found: 3
Ports tested: 9
Open ports found: 4
Elapsed time: 12.34 seconds

Scan complete. Found 3 live host(s).
```

With manual subnet:

```text
NetScout v4.1

Network Information
-------------------
Target Network: 192.168.1.0/24

Scan Results
------------
Scanning 254 hosts on 192.168.1.0/24...

IP Address   | Hostname     | MAC Address       | Vendor  | Device Type | Status | Open Ports
-------------+--------------+-------------------+---------+-------------+--------+--------------------------
192.168.1.1  | router.local | A0:F3:C1:12:34:56 | TP-Link | Router      | Live   | 53 (DNS), 80 (HTTP)
192.168.1.25 | laptop.local | D0:67:E5:AA:BB:CC | Dell    | Windows PC  | Live   | 445 (SMB), 3389 (RDP)
192.168.1.42 | Unknown      | Unknown           | Unknown | Unknown     | Live   | None

Device Inventory
----------------
Router: 1
Windows PC: 1
Unknown: 1

Scan Summary
------------
Hosts scanned: 254
Live hosts found: 3
Ports tested: 9
Open ports found: 4
Elapsed time: 12.34 seconds

Scan complete. Found 3 live host(s).
```

With card view:

```text
NetScout v4.1

Network Information
-------------------
Target Network: 192.168.1.0/24

Scan Results
------------
Scanning 254 hosts on 192.168.1.0/24...

Device 1
--------
IP Address: 192.168.1.193
Hostname: DESKTOP-OQFOLL1.lan
MAC Address: Unknown
Vendor: Unknown
Device Type: Windows PC
Status: Live
Open Ports:
  - 135 (MSRPC)
  - 139 (NetBIOS)
  - 445 (SMB)

Device Inventory
----------------
Windows PC: 1

Scan Summary
------------
Hosts scanned: 254
Live hosts found: 1
Ports tested: 9
Open ports found: 3
Elapsed time: 12.34 seconds

Scan complete. Found 1 live host(s).
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
9. `vendor.py` normalizes each MAC address and uses the first 3 bytes, called the OUI, to identify common hardware vendors.
10. `scanner.py` uses simple rules to infer a device type from hostname, vendor, and open ports.
11. `ports.py` checks common TCP ports, or the ports provided with `--ports`.
12. The CLI prints clean section headers for network information, scan results, summary, history comparison, and export results.
13. The CLI prints each live host in the selected view: table by default, or compact device cards with `--view cards`.
14. The CLI prints a device inventory summary that counts live hosts by device type.
15. The CLI prints a scan summary with host, port, and elapsed-time statistics.
16. If `--export` is used, `export.py` saves CSV, JSON, and/or HTML report files.
17. If `--open-report` is used with an HTML export, the CLI opens the report with Python's `webbrowser` module.
18. If `--save-history` is used, `history.py` saves the scan to a timestamped JSON file.
19. If `--compare-last` is used, `history.py` compares the current scan with the newest previous history file.

## Device Intelligence Notes

MAC address detection depends on the local ARP table. This works best for devices on your own local network after they have responded to ping. Devices outside your local network, devices blocked by firewall rules, or hosts that do not appear in ARP will show `Unknown`.

Vendor detection normalizes MAC addresses before lookup, so formats like `AA:BB:CC:11:22:33` and `aa-bb-cc-11-22-33` are treated the same. NetScout matches the first 3 bytes of the MAC address against the built-in OUI table. The table includes common prefixes for Apple, Google, Ring, Amazon, TP-Link, ASUS, Netgear, Ubiquiti, Samsung, Intel, Dell, HP, Microsoft, VMware, Raspberry Pi, Aqara, Cisco, and Synology. If no prefix matches, NetScout shows `Unknown`.

Device type detection uses simple rules in `scanner.py`. Hostnames containing `desktop` or `pc`, or devices with Windows ports 135, 139, or 445 open, show `Windows PC`. Hostnames containing `iphone`, `pixel`, or `android` show `Phone`. Hostnames containing `ring`, `cam`, or `camera` show `Camera`. Hostnames containing `aqara` or `hub` show `Smart Hub`. Hostnames containing `router` or `gateway`, or devices with ports 53, 80, or 443 open, show `Router`. Hostnames containing `printer`, or devices with port 9100 open, show `Printer`. Vendor names also help as fallback hints, such as Ring for cameras, Aqara for smart hubs, and TP-Link, ASUS, Netgear, or Ubiquiti for routers. If no rule matches, NetScout shows `Unknown`.

The Device Inventory section counts the `device_type` values from the current scan results. Known device types are shown alphabetically, and `Unknown` appears last.

## Safety Note

Only scan networks you own or have permission to test. Even a basic ping scan can be unwanted traffic on networks you do not control.
