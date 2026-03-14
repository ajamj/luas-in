import pytest
import socket
import struct
from unittest.mock import MagicMock

@pytest.fixture
def mock_socket():
    return MagicMock(spec=socket.socket)

@pytest.fixture
def protocol_header():
    def _header(ptype, length):
        return struct.pack("!BI", ptype, length)
    return _header
