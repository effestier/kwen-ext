"""Tests for HTTP client and URL validation."""

import pytest
from kwen_ext.utils.http import validate_url


class TestValidateUrl:
    def test_valid_https(self):
        assert validate_url("https://example.com") is True

    def test_valid_http(self):
        assert validate_url("http://example.com") is True

    def test_blocks_localhost(self):
        with pytest.raises(ValueError, match="Blocked host"):
            validate_url("http://localhost:8080")

    def test_blocks_127(self):
        with pytest.raises(ValueError, match="Blocked"):
            validate_url("http://127.0.0.1/admin")

    def test_blocks_private_ip(self):
        with pytest.raises(ValueError, match="Blocked"):
            validate_url("http://192.168.1.1/admin")

    def test_blocks_10_x(self):
        with pytest.raises(ValueError, match="Blocked"):
            validate_url("http://10.0.0.1/admin")

    def test_blocks_file_scheme(self):
        with pytest.raises(ValueError, match="Blocked scheme"):
            validate_url("file:///etc/passwd")

    def test_blocks_ftp_scheme(self):
        with pytest.raises(ValueError, match="Blocked scheme"):
            validate_url("ftp://example.com")

    def test_blocks_metadata(self):
        with pytest.raises(ValueError, match="Blocked"):
            validate_url("http://169.254.169.254/metadata")
