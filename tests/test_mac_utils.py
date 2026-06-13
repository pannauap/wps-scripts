"""Tests for MAC address utilities."""

import re

import pytest

from wps_lib.mac_utils import (
    is_valid_mac,
    normalize_mac,
    parse_iwconfig_output,
    random_mac,
)


class TestRandomMac:
    """Tests for random MAC address generation."""

    def test_format(self):
        mac = random_mac()
        assert re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', mac)

    def test_oui_prefix(self):
        """Generated MACs should have the Xensource OUI prefix."""
        mac = random_mac()
        assert mac.startswith("00:16:3e:")

    def test_randomness(self):
        """Multiple calls should produce different MACs (with high probability)."""
        macs = {random_mac() for _ in range(100)}
        # With 3 random bytes, collision probability is extremely low
        assert len(macs) > 90

    def test_second_octet_range(self):
        """4th byte should be in range 0x00-0x7f."""
        for _ in range(100):
            mac = random_mac()
            fourth_byte = int(mac.split(':')[3], 16)
            assert 0x00 <= fourth_byte <= 0x7f

    def test_last_bytes_range(self):
        """5th and 6th bytes should be in range 0x00-0xff."""
        for _ in range(50):
            mac = random_mac()
            parts = mac.split(':')
            assert 0x00 <= int(parts[4], 16) <= 0xff
            assert 0x00 <= int(parts[5], 16) <= 0xff


class TestIsValidMac:
    """Tests for MAC address validation."""

    def test_colon_separated(self):
        assert is_valid_mac("00:16:3e:4a:bf:12") is True

    def test_hyphen_separated(self):
        assert is_valid_mac("00-16-3E-4A-BF-12") is True

    def test_no_separator(self):
        assert is_valid_mac("00163e4abf12") is True

    def test_uppercase(self):
        assert is_valid_mac("AA:BB:CC:DD:EE:FF") is True

    def test_mixed_case(self):
        assert is_valid_mac("aA:bB:cC:dD:eE:fF") is True

    def test_invalid_too_short(self):
        assert is_valid_mac("00:16:3e:4a:bf") is False

    def test_invalid_too_long(self):
        assert is_valid_mac("00:16:3e:4a:bf:12:34") is False

    def test_invalid_chars(self):
        assert is_valid_mac("GG:16:3e:4a:bf:12") is False

    def test_empty_string(self):
        assert is_valid_mac("") is False

    def test_invalid_format(self):
        assert is_valid_mac("00.16.3e.4a.bf.12") is False


class TestNormalizeMac:
    """Tests for MAC address normalization."""

    def test_already_normalized(self):
        assert normalize_mac("00:16:3e:4a:bf:12") == "00:16:3e:4a:bf:12"

    def test_uppercase_to_lower(self):
        assert normalize_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"

    def test_hyphen_to_colon(self):
        assert normalize_mac("00-16-3E-4A-BF-12") == "00:16:3e:4a:bf:12"

    def test_no_separator(self):
        assert normalize_mac("00163E4ABF12") == "00:16:3e:4a:bf:12"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            normalize_mac("invalid")

    def test_too_short_raises(self):
        with pytest.raises(ValueError):
            normalize_mac("00:16:3e")


class TestParseIwconfigOutput:
    """Tests for iwconfig output parsing."""

    def test_monitor_interface(self):
        output = "mon0      IEEE 802.11bgn  Mode:Monitor  Frequency:2.412 GHz\n"
        monitors, interfaces = parse_iwconfig_output(output)
        assert "mon0" in monitors
        assert len(interfaces) == 0

    def test_managed_interface_connected(self):
        output = 'wlan0     IEEE 802.11bgn  ESSID:"MyNetwork"\n'
        monitors, interfaces = parse_iwconfig_output(output)
        assert len(monitors) == 0
        assert "wlan0" in interfaces
        assert interfaces["wlan0"] == 1

    def test_managed_interface_disconnected(self):
        output = "wlan0     IEEE 802.11bgn  ESSID:off/any\n"
        monitors, interfaces = parse_iwconfig_output(output)
        assert len(monitors) == 0
        assert "wlan0" in interfaces
        assert interfaces["wlan0"] == 0

    def test_wired_interface_ignored(self):
        output = "eth0      no wireless extensions.\n"
        monitors, interfaces = parse_iwconfig_output(output)
        assert len(monitors) == 0
        assert len(interfaces) == 0

    def test_mixed_output(self):
        output = (
            'wlan0     IEEE 802.11bgn  ESSID:"Home"\n'
            "          Mode:Managed  Frequency:2.437 GHz\n"
            "\n"
            "mon0      IEEE 802.11bgn  Mode:Monitor  Frequency:2.412 GHz\n"
            "          Retry short limit:7\n"
            "\n"
            "eth0      no wireless extensions.\n"
        )
        monitors, interfaces = parse_iwconfig_output(output)
        assert "mon0" in monitors
        assert "wlan0" in interfaces
        assert interfaces["wlan0"] == 1
        assert "eth0" not in interfaces

    def test_empty_output(self):
        monitors, interfaces = parse_iwconfig_output("")
        assert monitors == []
        assert interfaces == {}

    def test_multiple_monitors(self):
        output = (
            "mon0      IEEE 802.11bgn  Mode:Monitor  Frequency:2.412 GHz\n"
            "mon1      IEEE 802.11bgn  Mode:Monitor  Frequency:5.180 GHz\n"
        )
        monitors, interfaces = parse_iwconfig_output(output)
        assert "mon0" in monitors
        assert "mon1" in monitors
        assert len(monitors) == 2
