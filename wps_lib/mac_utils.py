"""MAC address utilities.

Ported from reaver-spoof.py to Python 3.
Provides MAC address generation and validation utilities.
"""

import re
from random import randint


def random_mac():
    """Generate a random MAC address with Xensource OUI (00:16:3e).

    The OUI prefix 00:16:3e is commonly used for virtualization
    (Xen, KVM) to avoid conflicts with real hardware.

    Returns:
        MAC address string in colon-separated format (e.g., '00:16:3e:4a:bf:12').
    """
    mac = [0x00, 0x16, 0x3e,
           randint(0x00, 0x7f),
           randint(0x00, 0xff),
           randint(0x00, 0xff)]
    return ':'.join("%02x" % x for x in mac)


def is_valid_mac(mac_str):
    """Validate a MAC address string.

    Accepts formats with colons, hyphens, or no separators.

    Args:
        mac_str: MAC address string to validate.

    Returns:
        True if the MAC address is valid, False otherwise.
    """
    patterns = [
        r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$',
        r'^([0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2}$',
        r'^[0-9a-fA-F]{12}$',
    ]
    return any(re.match(p, mac_str) for p in patterns)


def normalize_mac(mac_str):
    """Normalize a MAC address to colon-separated lowercase format.

    Args:
        mac_str: MAC address string in any valid format.

    Returns:
        MAC address in 'xx:xx:xx:xx:xx:xx' format.

    Raises:
        ValueError: If the input is not a valid MAC address.
    """
    if not is_valid_mac(mac_str):
        raise ValueError("Invalid MAC address: %s" % mac_str)
    hex_only = re.sub(r'[^a-fA-F0-9]', '', mac_str).lower()
    return ':'.join(hex_only[i:i+2] for i in range(0, 12, 2))


def parse_iwconfig_output(output):
    """Parse iwconfig output to find wireless interfaces and monitors.

    Args:
        output: String output from the iwconfig command.

    Returns:
        Tuple of (monitors, interfaces) where:
            - monitors: list of interface names in Monitor mode
            - interfaces: dict mapping interface name to connection status
              (1 = connected/has ESSID, 0 = not connected)
    """
    monitors = []
    interfaces = {}

    for line in output.split('\n'):
        if len(line) == 0:
            continue
        if line[0] != ' ':
            wired_search = re.search(r'eth[0-9]|em[0-9]|p[1-9]p[1-9]', line)
            if not wired_search:
                iface = line[:line.find(' ')]
                if 'Mode:Monitor' in line:
                    monitors.append(iface)
                elif 'IEEE 802.11' in line:
                    if 'ESSID:"' in line:
                        interfaces[iface] = 1
                    else:
                        interfaces[iface] = 0
    return monitors, interfaces
