"""Tests for EasyBox WPS PIN generation."""

import pytest

from wps_lib.easybox import (
    derive_serial_number,
    derive_ssid,
    gen_pin,
    generate_easybox_pin,
    parse_bssid,
)
from wps_lib.pin_utils import validate_wps_pin


class TestParseBssid:
    """Tests for BSSID parsing."""

    def test_colon_separated(self):
        result = parse_bssid("38:22:9D:11:22:33")
        assert result == "38229D112233"

    def test_hyphen_separated(self):
        result = parse_bssid("38-22-9D-11-22-33")
        assert result == "38229D112233"

    def test_no_separator(self):
        result = parse_bssid("38229D112233")
        assert result == "38229D112233"

    def test_lowercase(self):
        result = parse_bssid("38:22:9d:11:22:33")
        assert result == "38229D112233"

    def test_invalid_too_short(self):
        with pytest.raises(ValueError):
            parse_bssid("38:22:9D:11:22")

    def test_invalid_too_long(self):
        with pytest.raises(ValueError):
            parse_bssid("38:22:9D:11:22:33:44")

    def test_invalid_characters(self):
        with pytest.raises(ValueError):
            parse_bssid("ZZ:22:9D:11:22:33")


class TestDeriveSerialNumber:
    """Tests for serial number derivation."""

    def test_known_mac(self):
        # MAC "38229D112233" -> last 4 hex chars "2233" -> int = 8755
        sn = derive_serial_number("38229D112233")
        assert sn == "R----08755"

    def test_format(self):
        sn = derive_serial_number("38229D112233")
        assert sn.startswith("R----")
        assert len(sn) == 10

    def test_zero_suffix(self):
        sn = derive_serial_number("38229D110000")
        assert sn == "R----00000"

    def test_max_suffix(self):
        sn = derive_serial_number("38229D11FFFF")
        assert sn == "R----65535"


class TestDeriveSsid:
    """Tests for SSID derivation."""

    def test_known_values(self):
        mac_str = "38229D112233"
        sn = "R----08755"
        ssid = derive_ssid(mac_str, sn)
        # mac_str[6:10] = "1122", sn[5] = '0', sn[9] = '5'
        assert "1122" in ssid
        assert ssid.startswith("Arcor|EasyBox|Vodafone-")

    def test_format(self):
        mac_str = "38229DAABBCC"
        sn = derive_serial_number(mac_str)
        ssid = derive_ssid(mac_str, sn)
        assert ssid.startswith("Arcor|EasyBox|Vodafone-")
        # 6 chars after prefix
        suffix = ssid.split("-")[1]
        assert len(suffix) == 6


class TestGenPin:
    """Tests for the gen_pin function."""

    def test_output_is_string_of_digits(self):
        mac_str = "38229D112233"
        sn = "R----08755"
        pin = gen_pin(mac_str, sn)
        assert pin.isdigit()

    def test_pin_length(self):
        mac_str = "38229D112233"
        sn = "R----08755"
        pin = gen_pin(mac_str, sn)
        assert len(pin) == 8

    def test_pin_has_valid_checksum(self):
        mac_str = "38229D112233"
        sn = "R----08755"
        pin = gen_pin(mac_str, sn)
        assert validate_wps_pin(pin)

    def test_deterministic(self):
        mac_str = "38229D112233"
        sn = "R----08755"
        pin1 = gen_pin(mac_str, sn)
        pin2 = gen_pin(mac_str, sn)
        assert pin1 == pin2

    def test_different_macs_different_pins(self):
        sn1 = derive_serial_number("38229D112233")
        sn2 = derive_serial_number("38229DAABBCC")
        pin1 = gen_pin("38229D112233", sn1)
        pin2 = gen_pin("38229DAABBCC", sn2)
        assert pin1 != pin2

    def test_various_macs(self):
        test_macs = [
            "38229D112233",
            "38229D000000",
            "38229DFFFFFF",
            "AABBCCDDEEFF",
        ]
        for mac in test_macs:
            sn = derive_serial_number(mac)
            pin = gen_pin(mac, sn)
            assert pin.isdigit()
            assert len(pin) == 8
            assert validate_wps_pin(pin)


class TestGenerateEasyboxPin:
    """Tests for the full EasyBox PIN generation pipeline."""

    def test_full_pipeline(self):
        result = generate_easybox_pin("38:22:9D:11:22:33")
        assert 'pin' in result
        assert 'serial_number' in result
        assert 'ssid' in result

    def test_pin_is_valid(self):
        result = generate_easybox_pin("38:22:9D:11:22:33")
        assert validate_wps_pin(result['pin'])

    def test_serial_number_format(self):
        result = generate_easybox_pin("38:22:9D:11:22:33")
        assert result['serial_number'].startswith("R----")
        assert len(result['serial_number']) == 10

    def test_ssid_format(self):
        result = generate_easybox_pin("38:22:9D:11:22:33")
        assert result['ssid'].startswith("Arcor|EasyBox|Vodafone-")

    def test_invalid_bssid_raises(self):
        with pytest.raises(ValueError):
            generate_easybox_pin("invalid")

    def test_consistency(self):
        """Same BSSID should produce same results."""
        r1 = generate_easybox_pin("38:22:9D:11:22:33")
        r2 = generate_easybox_pin("38:22:9D:11:22:33")
        assert r1 == r2

    def test_different_formats_same_result(self):
        """Different BSSID formats should produce the same PIN."""
        r1 = generate_easybox_pin("38:22:9D:11:22:33")
        r2 = generate_easybox_pin("38-22-9D-11-22-33")
        assert r1['pin'] == r2['pin']
