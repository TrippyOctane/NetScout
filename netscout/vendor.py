"""Hardware vendor lookup helpers based on MAC address prefixes."""

from __future__ import annotations


# A MAC address starts with a 3-byte prefix called an OUI.
# Vendors buy OUIs, so the prefix can often tell us who made the hardware.
#
# This table is intentionally simple and easy to expand. Add more entries by
# using the first six hexadecimal characters of a MAC address as the key.
OUI_VENDOR_MAP = {
    # Apple
    "0016CB": "Apple",
    "001B63": "Apple",
    "0023DF": "Apple",
    "28CFDA": "Apple",
    "3C0754": "Apple",
    "40A6D9": "Apple",
    "7CD1C3": "Apple",
    "A4C361": "Apple",
    "ACBC32": "Apple",
    "D0E140": "Apple",
    "F0D1A9": "Apple",
    # Google
    "3C5AB4": "Google",
    "546009": "Google",
    "6CA6F3": "Google",
    "A47733": "Google",
    "F4F5D8": "Google",
    # Ring
    "5C41E7": "Ring",
    "60B5E8": "Ring",
    "90A72F": "Ring",
    "B0CE18": "Ring",
    "FC49E3": "Ring",
    # Amazon
    "0C47C9": "Amazon",
    "18B430": "Amazon",
    "3C28EF": "Amazon",
    "44F4E7": "Amazon",
    "68DBF5": "Amazon",
    "AC63BE": "Amazon",
    # ASUS
    "001731": "ASUS",
    "049226": "ASUS",
    "10BF48": "ASUS",
    "2C4D54": "ASUS",
    "AC220B": "ASUS",
    "D017C2": "ASUS",
    # Cisco
    "00000C": "Cisco",
    "001BD4": "Cisco",
    "0026CB": "Cisco",
    "4C0082": "Cisco",
    "F87B20": "Cisco",
    # Dell
    "001143": "Dell",
    "001422": "Dell",
    "00188B": "Dell",
    "002219": "Dell",
    "18A99B": "Dell",
    "5CF9DD": "Dell",
    "D067E5": "Dell",
    "F8B156": "Dell",
    # HP
    "001083": "HP",
    "001635": "HP",
    "002481": "HP",
    "186024": "HP",
    "2C44FD": "HP",
    "3C5282": "HP",
    "A0481C": "HP",
    "D89D67": "HP",
    # Intel
    "001B21": "Intel",
    "00216A": "Intel",
    "0C8BFD": "Intel",
    "3CFDFE": "Intel",
    "A0A8CD": "Intel",
    "F8B7E2": "Intel",
    # Microsoft
    "00155D": "Microsoft",
    "0050F2": "Microsoft",
    "28F076": "Microsoft",
    "7CED8D": "Microsoft",
    "C83F26": "Microsoft",
    # Netgear
    "00146C": "Netgear",
    "00223F": "Netgear",
    "20E52A": "Netgear",
    "6CB0CE": "Netgear",
    "9C3DCF": "Netgear",
    "A040A0": "Netgear",
    # Raspberry Pi
    "28CDCB": "Raspberry Pi",
    "B827EB": "Raspberry Pi",
    "DCA632": "Raspberry Pi",
    "E45F01": "Raspberry Pi",
    # Samsung
    "002454": "Samsung",
    "08D42B": "Samsung",
    "5CF8A1": "Samsung",
    "78F882": "Samsung",
    "C8D7B0": "Samsung",
    # Synology
    "001132": "Synology",
    "002232": "Synology",
    "9009D0": "Synology",
    # TP-Link
    "0C8063": "TP-Link",
    "14CC20": "TP-Link",
    "50C7BF": "TP-Link",
    "98DAC4": "TP-Link",
    "A0F3C1": "TP-Link",
    "C46E1F": "TP-Link",
    "F4F26D": "TP-Link",
    # Ubiquiti
    "0418D6": "Ubiquiti",
    "24A43C": "Ubiquiti",
    "44D9E7": "Ubiquiti",
    "68D79A": "Ubiquiti",
    "78D38D": "Ubiquiti",
    "DC9FDB": "Ubiquiti",
    "F09FC2": "Ubiquiti",
    # VMware
    "000569": "VMware",
    "000C29": "VMware",
    "001C14": "VMware",
    "005056": "VMware",
    # Aqara
    "04CF8C": "Aqara",
    "54EF44": "Aqara",
    "5C0272": "Aqara",
    "7C49EB": "Aqara",
}


def normalize_oui(mac_address: str) -> str:
    """Return the first six hexadecimal characters from a MAC address.

    The first six hex characters are the first three bytes of the MAC address,
    also called the OUI.

    >>> normalize_oui("a4:c3:61:12:34:56")
    'A4C361'
    >>> normalize_oui("A4-C3-61-12-34-56")
    'A4C361'
    """
    hex_digits = "".join(
        character for character in mac_address.upper() if character in "0123456789ABCDEF"
    )
    return hex_digits[:6]


def lookup_vendor(mac_address: str) -> str:
    """Return a hardware vendor name for a MAC address, or Unknown.

    >>> lookup_vendor("a4:c3:61:12:34:56")
    'Apple'
    >>> lookup_vendor("3c-5a-b4-aa-bb-cc")
    'Google'
    >>> lookup_vendor("12:34:56:78:90:ab")
    'Unknown'
    """
    if mac_address == "Unknown":
        return "Unknown"

    oui = normalize_oui(mac_address)
    return OUI_VENDOR_MAP.get(oui, "Unknown")
