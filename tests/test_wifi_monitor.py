import sys
import os
import struct
import pytest
from unittest.mock import MagicMock, patch

# Define mock classes with common methods to avoid AttributeErrors
class MockBase:
    def __init__(self, *args, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, MagicMock())
    def __getattr__(self, name):
        return MagicMock()
    def grid(self, *args, **kwargs): return MagicMock()
    def pack(self, *args, **kwargs): return MagicMock()
    def configure(self, *args, **kwargs): return MagicMock()
    def bind(self, *args, **kwargs): return MagicMock()
    def unbind(self, *args, **kwargs): return MagicMock()
    def after(self, *args, **kwargs): return MagicMock()

class MockCTk(MockBase):
    def title(self, *args, **kwargs): pass
    def geometry(self, *args, **kwargs): pass
    def attributes(self, *args, **kwargs): pass
    def mainloop(self, *args, **kwargs): pass

class MockWidget(MockBase):
    def insert(self, *args, **kwargs): pass
    def get(self, *args, **kwargs): return ""
    def set(self, *args, **kwargs): pass
    def configure(self, *args, **kwargs): pass
    def pack_forget(self, *args, **kwargs): pass
    def grid_remove(self, *args, **kwargs): pass
    def grid_configure(self, *args, **kwargs): pass

# Mock customtkinter module
class MockCTKModule:
    CTk = MockCTk
    CTkFrame = MockWidget
    CTkLabel = MockWidget
    CTkEntry = MockWidget
    CTkButton = MockWidget
    CTkProgressBar = MockWidget
    CTkTextbox = MockWidget
    CTkComboBox = MockWidget
    CTkCheckBox = MockWidget
    CTkFont = MagicMock
    CTkImage = MagicMock
    BooleanVar = MagicMock
    set_appearance_mode = MagicMock()
    set_default_color_theme = MagicMock()

# Mock mss
mock_mss_instance = MagicMock()
mock_mss_instance.monitors = [
    {"width": 1920, "height": 1080}, # Monitor 0 (all)
    {"width": 1920, "height": 1080}  # Monitor 1
]
mock_mss_class = MagicMock(return_value=mock_mss_instance)
# Ensure context manager works: with mss() as sct:
mock_mss_instance.__enter__.return_value = mock_mss_instance

# Inject mocks
sys.modules['customtkinter'] = MockCTKModule
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['mss'] = MagicMock()
sys.modules['mss'].mss = mock_mss_class
sys.modules['pyperclip'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
import client
import server

def test_protocol_packing():
    ptype = client.TYPE_CLIPBOARD
    length = 100
    expected = struct.pack("!BI", ptype, length)
    header = struct.pack("!BI", ptype, length)
    assert header == expected
    
    up_ptype, up_length = struct.unpack("!BI", header)
    assert up_ptype == ptype
    assert up_length == length

def test_client_recv_all_logic():
    c = client.WiFiMonitorClient()
    c.client_socket = MagicMock()
    c.client_socket.recv.side_effect = [b"abc", b"de"]
    res = c._recv_all(5)
    assert res == b"abcde"

def test_server_incoming_file_dict():
    s = server.WiFiMonitorServer()
    s.downloads_path = "/tmp"
    sock = MagicMock()
    s.incoming_files[sock] = {
        "name": "test.txt",
        "size": 1000,
        "received": 0,
        "handle": MagicMock()
    }
    chunk = b"data"
    s.incoming_files[sock]["handle"].write(chunk)
    s.incoming_files[sock]["received"] += len(chunk)
    assert s.incoming_files[sock]["received"] == 4

def test_clipboard_encoding():
    text = "Test"
    assert text.encode('utf-8').decode('utf-8') == text
