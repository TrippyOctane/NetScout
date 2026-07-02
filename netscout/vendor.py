"""Hardware vendor lookup helpers based on MAC address prefixes."""

from __future__ import annotations


# A MAC address starts with a 3-byte prefix called an OUI.
# Vendors buy OUIs, so the prefix can often tell us who made the hardware.
#
# This table is intentionally small and easy to expand. Add more entries by
# using the first six hexadecimal characters of a MAC address as the key.
OUI_VENDOR_MAP = {
    # Apple
    "0016CB": "Apple",
    "001B63": "Apple",
    "0023DF": "Apple",
    "3C0754": "Apple",
    "A4C361": "Apple",
    "F0D1A9": "Apple",
    # ASUS
    "001731": "ASUS",
    "049226": "ASUS",
    "10BF48": "ASUS",
    "AC220B": "ASUS",
    # Cisco
    "00000C": "Cisco",
    "001BD4": "Cisco",
    "0026CB": "Cisco",
    "4C0082": "Cisco",
    "F87B20": "Cisco",
    # Dell
    "001422": "Dell",
    "00188B": "Dell",
    "002219": "Dell",
    "D067E5": "Dell",
    "F8B156": "Dell",
    # HP
    "001635": "HP",
    "002481": "HP",
    "2C44FD": "HP",
    "3C5282": "HP",
    "D89D67": "HP",
    # Intel
    "001B21": "Intel",
    "00216A": "Intel",
    "3CFDFE": "Intel",
    "A0A8CD": "Intel",
    "F4F5D8": "Intel",
    # Microsoft
    "00155D": "Microsoft",
    "0050F2": "Microsoft",
    "7CED8D": "Microsoft",
    # Netgear
    "00146C": "Netgear",
    "00223F": "Netgear",
    "9C3DCF": "Netgear",
    "A040A0": "Netgear",
    # Raspberry Pi
    "B827EB": "Raspberry Pi",
    "DCA632": "Raspberry Pi",
    "E45F01": "Raspberry Pi",
    # Synology
    "001132": "Synology",
    "002232": "Synology",
    "9009D0": "Synology",
    # TP-Link
    "14CC20": "TP-Link",
    "50C7BF": "TP-Link",
    "A0F3C1": "TP-Link",
    "C46E1F": "TP-Link",
    # Ubiquiti
    "0418D6": "Ubiquiti",
    "24A43C": "Ubiquiti",
    "44D9E7": "Ubiquiti",
    "F09FC2": "Ubiquiti",
    # VMware
    "000569": "VMware",
    "000C29": "VMware",
    "001C14": "VMware",
    "005056": "VMware",
}


def normalize_oui(mac_address: str) -> str:
    """Return the first six hexadecimal characters from a MAC address."""
    hex_digits = "".join(
        character for character in mac_address.upper() if character in "0123456789ABCDEF"
    )
    return hex_digits[:6]


def lookup_vendor(mac_address: str) -> str:
    """Return a hardware vendor name for a MAC address, or Unknown."""
    if mac_address == "Unknown":
        return "Unknown"

    oui = normalize_oui(mac_address)
    return OUI_VENDOR_MAP.get(oui, "Unknown")
