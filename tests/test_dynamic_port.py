"""Tests for dynamic port discovery (Issue #42)."""
import os
import socket
import unittest
from unittest.mock import patch


class TestGetFreePort(unittest.TestCase):
    """Test the get_free_port() helper from api_entry."""

    def _get_free_port(self, dev_mode=False):
        """Import and call get_free_port from scripts.api_entry."""
        from scripts.api_entry import get_free_port
        return get_free_port(dev_mode=dev_mode)

    def test_get_free_port_returns_valid_port(self):
        """Prod mode: port should be a valid ephemeral port (> 1024) and bindable."""
        port = self._get_free_port(dev_mode=False)
        self.assertIsInstance(port, int)
        self.assertGreater(port, 1024)

        # Verify the port is actually available by binding to it
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
        finally:
            sock.close()

    def test_get_free_port_unique(self):
        """Two consecutive calls should return different ports."""
        port1 = self._get_free_port(dev_mode=False)
        port2 = self._get_free_port(dev_mode=False)
        self.assertNotEqual(port1, port2)

    def test_dev_mode_returns_8000(self):
        """Dev mode should always return port 8000."""
        port = self._get_free_port(dev_mode=True)
        self.assertEqual(port, 8000)


if __name__ == '__main__':
    unittest.main()
