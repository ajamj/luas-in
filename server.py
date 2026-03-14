import sys
import socket
import threading
import time
import io
import struct
import os
import customtkinter as ctk
import pyperclip
from mss import mss
from PIL import Image
from tkinter import filedialog

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Protocol Types
TYPE_FRAME = 0x00
TYPE_CLIPBOARD = 0x01
TYPE_FILE_START = 0x02
TYPE_FILE_CHUNK = 0x03
TYPE_FILE_END = 0x04

class WiFiMonitorServer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WiFiMonitor - Windows Server Pro")
        self.geometry("500x750")
        
        # Core State
        self.streaming = False
        self.clients = []
        self.port = 5000
        self.password = "1234"
        self.quality = 70
        self.server_socket = None
        self.last_clipboard = ""
        self.downloads_path = os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(self.downloads_path):
            os.makedirs(self.downloads_path)
        self.incoming_files = {} # socket -> file_info
        
        self.init_ui()
        self.add_log("Server Pro initialized. Ready to start.")

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Configuration Frame
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")
        self.config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.config_frame, text="Configuration", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=10)

        ctk.CTkLabel(self.config_frame, text="Port:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.port_input = ctk.CTkEntry(self.config_frame)
        self.port_input.insert(0, "5000")
        self.port_input.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.config_frame, text="Password:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.pass_input = ctk.CTkEntry(self.config_frame, show="*")
        self.pass_input.insert(0, "1234")
        self.pass_input.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.config_frame, text="Target Monitor:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.monitor_combo = ctk.CTkComboBox(self.config_frame, values=self.get_monitors())
        self.monitor_combo.set(self.get_monitors()[0])
        self.monitor_combo.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        self.lbl_ext_info = ctk.CTkLabel(self.config_frame, text="💡 For Extended Mode, ensure Windows detects a 2nd display.", font=ctk.CTkFont(size=10, slant="italic"), text_color="gray")
        self.lbl_ext_info.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")

        # Feature Toggles
        self.features_frame = ctk.CTkFrame(self)
        self.features_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        self.features_frame.grid_columnconfigure((0, 1), weight=1)

        self.cb_sync_var = ctk.BooleanVar(value=True)
        self.cb_sync = ctk.CTkCheckBox(self.features_frame, text="Clipboard Sync", variable=self.cb_sync_var)
        self.cb_sync.grid(row=0, column=0, padx=10, pady=10)

        self.btn_send_file = ctk.CTkButton(self.features_frame, text="Send File", command=self.send_file_dialog, state="disabled")
        self.btn_send_file.grid(row=0, column=1, padx=10, pady=10)

        # Status and Controls
        self.btn_toggle = ctk.CTkButton(self, text="Start Server", command=self.toggle_server, fg_color="#2ecc71", hover_color="#27ae60")
        self.btn_toggle.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.status_frame.grid_columnconfigure((0, 1), weight=1)

        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Status: Stopped", text_color="#e74c3c")
        self.lbl_status.grid(row=0, column=0, padx=5, pady=5)

        self.lbl_clients = ctk.CTkLabel(self.status_frame, text="Connected Clients: 0")
        self.lbl_clients.grid(row=0, column=1, padx=5, pady=5)

        # Logs
        ctk.CTkLabel(self, text="System Logs").grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        self.log_area = ctk.CTkTextbox(self)
        self.log_area.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.log_area.configure(state="disabled")

    def get_monitors(self):
        with mss() as sct:
            monitors = []
            for i, monitor in enumerate(sct.monitors):
                label = f"Monitor {i} ({monitor['width']}x{monitor['height']})" if i > 0 else "All Monitors"
                monitors.append(label)
            return monitors

    def add_log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"[{timestamp}] {msg}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def toggle_server(self):
        if not self.streaming:
            try:
                self.port = int(self.port_input.get())
                self.password = self.pass_input.get()
                self.start_server()
            except ValueError:
                self.add_log("Invalid port number.")
        else:
            self.stop_server()

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            
            self.streaming = True
            self.btn_send_file.configure(state="normal")
            self.update_status_ui(True)
            self.add_log(f"Server started on port {self.port}")
            
            threading.Thread(target=self.accept_clients, daemon=True).start()
            threading.Thread(target=self.capture_loop, daemon=True).start()
            threading.Thread(target=self.clipboard_loop, daemon=True).start()
            
        except Exception as e:
            self.add_log(f"Error starting server: {e}")

    def stop_server(self):
        self.streaming = False
        self.btn_send_file.configure(state="disabled")
        if self.server_socket:
            try: self.server_socket.shutdown(socket.SHUT_RDWR)
            except: pass
            self.server_socket.close()
        for client in self.clients:
            try: client.close()
            except: pass
        self.clients = []
        self.lbl_clients.configure(text="Connected Clients: 0")
        self.update_status_ui(False)
        self.add_log("Server stopped.")

    def update_status_ui(self, running):
        if running:
            self.lbl_status.configure(text="Status: Running", text_color="#2ecc71")
            self.btn_toggle.configure(text="Stop Server", fg_color="#e74c3c", hover_color="#c0392b")
        else:
            self.lbl_status.configure(text="Status: Stopped", text_color="#e74c3c")
            self.btn_toggle.configure(text="Start Server", fg_color="#2ecc71", hover_color="#27ae60")

    def send_packet(self, ptype, data):
        # Protocol: [1 byte type][4 bytes length][data]
        header = struct.pack("!BI", ptype, len(data))
        packet = header + data
        disconnected = []
        for client in self.clients:
            try:
                client.sendall(packet)
            except:
                disconnected.append(client)
        
        for client in disconnected:
            if client in self.clients:
                self.clients.remove(client)
        
        if disconnected:
            self.after(0, lambda: self.lbl_clients.configure(text=f"Connected Clients: {len(self.clients)}"))

    def accept_clients(self):
        while self.streaming:
            try:
                client_socket, addr = self.server_socket.accept()
                # Initial auth
                data = client_socket.recv(1024).decode()
                if data == self.password:
                    client_socket.send("OK".encode())
                    self.clients.append(client_socket)
                    self.after(0, lambda: self.lbl_clients.configure(text=f"Connected Clients: {len(self.clients)}"))
                    self.add_log(f"Client {addr} connected.")
                    threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
                else:
                    client_socket.send("FAIL".encode())
                    client_socket.close()
            except: break

    def handle_client(self, client_socket, addr):
        while self.streaming:
            try:
                header = self._recv_all(client_socket, 5)
                if not header: break
                ptype, size = struct.unpack("!BI", header)
                data = self._recv_all(client_socket, size)
                if data is None: break

                if ptype == TYPE_CLIPBOARD:
                    text = data.decode('utf-8')
                    pyperclip.copy(text)
                    self.add_log(f"Clipboard received from {addr}")
                elif ptype == TYPE_FILE_START:
                    decoded = data.decode('utf-8')
                    name, fsize = decoded.split("|")
                    self.incoming_files[client_socket] = {
                        "name": name,
                        "size": int(fsize),
                        "received": 0,
                        "handle": open(os.path.join(self.downloads_path, name), "wb")
                    }
                    self.add_log(f"Receiving file '{name}' from {addr}")
                elif ptype == TYPE_FILE_CHUNK:
                    if client_socket in self.incoming_files:
                        self.incoming_files[client_socket]["handle"].write(data)
                        self.incoming_files[client_socket]["received"] += len(data)
                elif ptype == TYPE_FILE_END:
                    if client_socket in self.incoming_files:
                        self.incoming_files[client_socket]["handle"].close()
                        self.add_log(f"File '{self.incoming_files[client_socket]['name']}' saved.")
                        del self.incoming_files[client_socket]
            except Exception as e:
                self.add_log(f"Client {addr} error: {e}")
                break
        
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        self.after(0, lambda: self.lbl_clients.configure(text=f"Connected Clients: {len(self.clients)}"))
        self.add_log(f"Client {addr} disconnected.")
        client_socket.close()

    def _recv_all(self, sock, n):
        data = bytearray()
        while len(data) < n:
            try:
                packet = sock.recv(n - len(data))
                if not packet: return None
                data.extend(packet)
            except: return None
        return data

    def capture_loop(self):
        with mss() as sct:
            while self.streaming:
                if not self.clients:
                    time.sleep(0.5)
                    continue
                try:
                    mon_str = self.monitor_combo.get()
                    monitor_idx = 0 if mon_str == "All Monitors" else int(mon_str.split(" ")[1])
                    if monitor_idx >= len(sct.monitors): monitor_idx = 0
                    
                    img = sct.grab(sct.monitors[monitor_idx])
                    pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
                    buffer = io.BytesIO()
                    pil_img.save(buffer, format="JPEG", quality=self.quality)
                    self.send_packet(TYPE_FRAME, buffer.getvalue())
                    
                    # Target 30 FPS
                    time.sleep(1/30)
                except Exception as e:
                    time.sleep(1)

    def clipboard_loop(self):
        while self.streaming:
            if self.cb_sync_var.get() and self.clients:
                try:
                    current = pyperclip.paste()
                    if current and current != self.last_clipboard:
                        self.last_clipboard = current
                        self.send_packet(TYPE_CLIPBOARD, current.encode('utf-8'))
                        self.add_log("Clipboard synced to clients.")
                except: pass
            time.sleep(1)

    def send_file_dialog(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            threading.Thread(target=self.process_file_send, args=(filepath,), daemon=True).start()

    def process_file_send(self, filepath):
        try:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            self.add_log(f"Sending file: {filename} ({filesize} bytes)")
            
            # File Start: [filename|filesize]
            self.send_packet(TYPE_FILE_START, f"{filename}|{filesize}".encode('utf-8'))
            
            # Chunks
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024) # 64KB chunks
                    if not chunk: break
                    self.send_packet(TYPE_FILE_CHUNK, chunk)
                    # Small sleep to prevent network congestion
                    time.sleep(0.001)
            
            # File End
            self.send_packet(TYPE_FILE_END, b"DONE")
            self.add_log(f"File {filename} sent successfully.")
        except Exception as e:
            self.add_log(f"File send error: {e}")

if __name__ == "__main__":
    app = WiFiMonitorServer()
    app.mainloop()
