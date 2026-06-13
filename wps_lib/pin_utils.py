"""WPS PIN checksum and generation utilities.

Ported from belkin-wpspin.py and wpspin.py to Python 3.
The WPS PIN checksum algorithm is defined in the Wi-Fi Simple Configuration
specification and the Microsoft WCN-Netspec document.
"""


def wps_pin_checksum(pin):
    """Calculate the WPS PIN checksum digit.

    The checksum is the 8th digit of an 8-digit WPS PIN, computed
    from the first 7 digits using a weighted sum modulo 10.

    Args:
        pin: Integer representing the first 7 digits of the WPS PIN.

    Returns:
        Integer (0-9) representing the checksum digit.
    """
    accum = 0
    while pin:
        accum += 3 * (pin % 10)
        pin //= 10
        accum += pin % 10
        pin //= 10
    return (10 - accum % 10) % 10


def generate_pin_from_mac_last3(mac_last3_hex):
    """Generate a WPS PIN from the last 3 bytes of a MAC address.

    This is the algorithm used by belkin-wpspin.py and wpspin.py.

    Args:
        mac_last3_hex: 6-character hex string (last 3 bytes of MAC address).

    Returns:
        8-digit WPS PIN as a string.

    Raises:
        ValueError: If mac_last3_hex is not a valid 6-char hex string.
    """
    if len(mac_last3_hex) != 6:
        raise ValueError("mac_last3_hex must be exactly 6 hex characters")
    p = int(mac_last3_hex, 16) % 10000000
    checksum = wps_pin_checksum(p)
    return "%07d%d" % (p, checksum)


def validate_wps_pin(pin_str):
    """Validate a WPS PIN (8-digit string) using its checksum.

    Args:
        pin_str: 8-digit string representing the full WPS PIN.

    Returns:
        True if the PIN checksum is valid, False otherwise.
    """
    if len(pin_str) != 8 or not pin_str.isdigit():
        return False
    first_seven = int(pin_str[:7])
    expected_checksum = wps_pin_checksum(first_seven)
    return int(pin_str[7]) == expected_checksum
