"""Tests for WPS PIN checksum and generation utilities."""

import pytest

from wps_lib.pin_utils import (
    generate_pin_from_mac_last3,
    validate_wps_pin,
    wps_pin_checksum,
)


class TestWpsPinChecksum:
    """Tests for the wps_pin_checksum function."""

    def test_checksum_zero_input(self):
        assert wps_pin_checksum(0) == 0

    def test_checksum_known_values(self):
        # WPS spec: PIN 1234567 should have checksum 0
        # Let's verify with known PINs
        # 12345670 is a well-known valid WPS PIN
        assert wps_pin_checksum(1234567) == 0

    def test_checksum_range(self):
        """Checksum digit should always be 0-9."""
        for pin in [0, 1, 999999, 1000000, 5555555, 9999999]:
            checksum = wps_pin_checksum(pin)
            assert 0 <= checksum <= 9

    def test_checksum_various_pins(self):
        # Verify the checksum algorithm produces consistent results
        pin1 = 1234567
        pin2 = 7654321
        assert wps_pin_checksum(pin1) == wps_pin_checksum(pin1)
        assert isinstance(wps_pin_checksum(pin2), int)

    def test_checksum_single_digit(self):
        assert isinstance(wps_pin_checksum(1), int)
        assert 0 <= wps_pin_checksum(1) <= 9

    def test_checksum_max_seven_digits(self):
        assert isinstance(wps_pin_checksum(9999999), int)
        assert 0 <= wps_pin_checksum(9999999) <= 9

    def test_checksum_algorithm_correctness(self):
        """Manually verify the algorithm for PIN 1234567."""
        # Pin: 1234567
        # Iteration 1: accum += 3*(7) = 21; pin=123456; accum += 6 = 27; pin=12345
        # Iteration 2: accum += 3*(5) = 42; pin=1234; accum += 4 = 46; pin=123
        # Iteration 3: accum += 3*(3) = 55; pin=12; accum += 2 = 57; pin=1
        # Iteration 4: accum += 3*(1) = 60; pin=0; accum += 0 = 60; pin=0
        # checksum = (10 - 60 % 10) % 10 = (10 - 0) % 10 = 0
        assert wps_pin_checksum(1234567) == 0


class TestGeneratePinFromMac:
    """Tests for the generate_pin_from_mac_last3 function."""

    def test_known_mac_suffix(self):
        # MAC suffix "123456" -> int("123456", 16) = 1193046
        # 1193046 % 10000000 = 1193046
        pin = generate_pin_from_mac_last3("123456")
        assert len(pin) == 8
        assert pin.isdigit()
        # Verify checksum
        assert validate_wps_pin(pin)

    def test_output_format(self):
        pin = generate_pin_from_mac_last3("AABBCC")
        assert len(pin) == 8
        assert pin.isdigit()

    def test_various_mac_suffixes(self):
        test_macs = ["000000", "FFFFFF", "ABCDEF", "123456", "789ABC"]
        for mac in test_macs:
            pin = generate_pin_from_mac_last3(mac)
            assert len(pin) == 8
            assert pin.isdigit()
            assert validate_wps_pin(pin)

    def test_lowercase_hex(self):
        pin_upper = generate_pin_from_mac_last3("ABCDEF")
        pin_lower = generate_pin_from_mac_last3("abcdef")
        assert pin_upper == pin_lower

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError):
            generate_pin_from_mac_last3("12345")
        with pytest.raises(ValueError):
            generate_pin_from_mac_last3("1234567")

    def test_deterministic(self):
        """Same input should always produce the same PIN."""
        pin1 = generate_pin_from_mac_last3("AABBCC")
        pin2 = generate_pin_from_mac_last3("AABBCC")
        assert pin1 == pin2

    def test_pin_modulo_constraint(self):
        """First 7 digits should be < 10000000."""
        pin = generate_pin_from_mac_last3("FFFFFF")
        first_seven = int(pin[:7])
        assert first_seven < 10000000


class TestValidateWpsPin:
    """Tests for the validate_wps_pin function."""

    def test_valid_pin(self):
        # 12345670 is valid (checksum of 1234567 is 0)
        assert validate_wps_pin("12345670") is True

    def test_invalid_checksum(self):
        assert validate_wps_pin("12345671") is False

    def test_too_short(self):
        assert validate_wps_pin("1234567") is False

    def test_too_long(self):
        assert validate_wps_pin("123456700") is False

    def test_non_numeric(self):
        assert validate_wps_pin("1234567a") is False
        assert validate_wps_pin("abcdefgh") is False

    def test_empty_string(self):
        assert validate_wps_pin("") is False

    def test_generated_pins_are_valid(self):
        """All generated PINs should pass validation."""
        test_macs = ["000000", "111111", "AAAAAA", "FFFFFF"]
        for mac in test_macs:
            pin = generate_pin_from_mac_last3(mac)
            assert validate_wps_pin(pin)
