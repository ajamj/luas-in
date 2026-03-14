import sys
import socket
import threading
import struct
import io
import os
import customtkinter as ctk
import pyperclip
from PIL import Image, ImageTk

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Protocol Types
TYPE_FRAME = 0x00
TYPE_CLIPBOARD = 0x01
TYPE_FILE_START = 0x02
TYPE_FILE_CHUNK = 0x03
TYPE_FILE_END = 0x04

class WiFiMonitorClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WiFiMonitor - Client Pro")
        self.geometry("1100x850")
        
        # State
        self.client_socket = None
        self.running = False
        self.full_screen = False
        self.incoming_file = None
        self.downloads_path = os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(self.downloads_path):
            os.makedirs(self.downloads_path)
        
        self.init_ui()

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Control Frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.ip_input = ctk.CTkEntry(self.controls_frame, placeholder_text="Server IP")
        self.ip_input.insert(0, "127.0.0.1")
        self.ip_input.pack(side="left", padx=5, pady=10, fill="x", expand=True)
        
        self.port_input = ctk.CTkEntry(self.controls_frame, placeholder_text="Port", width=70)
        self.port_input.insert(0, "5000")
        self.port_input.pack(side="left", padx=5, pady=10)
        
        self.pass_input = ctk.CTkEntry(self.controls_frame, placeholder_text="Password", show="*", width=100)
        self.pass_input.insert(0, "1234")
        self.pass_input.pack(side="left", padx=5, pady=10)
        
        self.btn_connect = ctk.CTkButton(self.controls_frame, text="Connect", command=self.toggle_connection, width=100)
        self.btn_connect.pack(side="left", padx=5, pady=10)

        self.btn_fullscreen = ctk.CTkButton(self.controls_frame, text="Full Screen", command=self.toggle_fullscreen, width=100, fg_color="#34495e", hover_color="#2c3e50")
        self.btn_fullscreen.pack(side="left", padx=5, pady=10)

        # Display Area
        self.display_frame = ctk.CTkFrame(self, fg_color="black")
        self.display_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        self.display_label = ctk.CTkLabel(self.display_frame, text="No Signal", font=ctk.CTkFont(size=20))
        self.display_label.pack(expand=True, fill="both")

        # Status Bar
        self.status_bar = ctk.CTkFrame(self, height=30)
        self.status_bar.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.lbl_status = ctk.CTkLabel(self.status_bar, text="Disconnected")
        self.lbl_status.pack(side="left", padx=10)
        
        self.progress = ctk.CTkProgressBar(self.status_bar, width=200)
        self.progress.set(0)
        self.progress.pack(side="right", padx=10, pady=5)
        self.progress.pack_forget()

        # Bindings
        self.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.bind("<Escape>", lambda e: self.exit_fullscreen() if self.full_screen else None)

    def toggle_connection(self):
        if not self.running: self.start_connection()
        else: self.stop_connection()

    def start_connection(self):
        ip = self.ip_input.get()
        try:
            port = int(self.port_input.get())
            password = self.pass_input.get()
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            self.client_socket.connect((ip, port))
            self.client_socket.send(password.encode())
            resp = self.client_socket.recv(10).decode()
            if resp == "OK":
                self.running = True
                self.btn_connect.configure(text="Disconnect", fg_color="#e74c3c")
                self.lbl_status.configure(text=f"Connected to {ip}")
                self.client_socket.settimeout(None)
                threading.Thread(target=self.receive_loop, daemon=True).start()
            else: self.show_error("Invalid Password")
        except Exception as e: self.show_error(str(e))

    def stop_connection(self):
        self.running = False
        if self.client_socket:
            try: self.client_socket.close()
            except: pass
        self.btn_connect.configure(text="Connect", fg_color=["#3B8ED0", "#1F6AA5"])
        self.lbl_status.configure(text="Disconnected")
        self.display_label.configure(image=None, text="No Signal")

    def receive_loop(self):
        while self.running:
            try:
                # Header: [1 byte type][4 bytes length]
                header = self._recv_all(5)
                if not header: break
                ptype, size = struct.unpack("!BI", header)
                data = self._recv_all(size)
                if data is None: break
                
                if ptype == TYPE_FRAME:
                    image = Image.open(io.BytesIO(data))
                    self.after(0, lambda: self.update_frame(image))
                elif ptype == TYPE_CLIPBOARD:
                    text = data.decode('utf-8')
                    pyperclip.copy(text)
                    self.after(0, lambda: self.lbl_status.configure(text="Clipboard Synced"))
                elif ptype == TYPE_FILE_START:
                    decoded = data.decode('utf-8')
                    name, fsize = decoded.split("|")
                    self.incoming_file = {
                        "name": name, 
                        "size": int(fsize), 
                        "received": 0, 
                        "handle": open(os.path.join(self.downloads_path, name), "wb")
                    }
                    self.after(0, self.show_progress)
                elif ptype == TYPE_FILE_CHUNK:
                    if self.incoming_file:
                        self.incoming_file["handle"].write(data)
                        self.incoming_file["received"] += len(data)
                        progress = self.incoming_file["received"] / self.incoming_file["size"]
                        self.after(0, lambda p=progress: self.progress.set(p))
                elif ptype == TYPE_FILE_END:
                    if self.incoming_file:
                        self.incoming_file["handle"].close()
                        self.after(0, lambda n=self.incoming_file["name"]: self.finish_file(n))
                        self.incoming_file = None
            except Exception as e:
                break
        self.after(0, self.stop_connection)

    def _recv_all(self, n):
        data = bytearray()
        while len(data) < n:
            try:
                packet = self.client_socket.recv(n - len(data))
                if not packet: return None
                data.extend(packet)
            except: return None
        return data

    def update_frame(self, pil_image):
        if not self.running: return
        w, h = self.display_frame.winfo_width(), self.display_frame.winfo_height()
        if w > 10 and h > 10:
            img_w, img_h = pil_image.size
            ratio = min(w/img_w, h/img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            pil_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(pil_image)
        self.display_label.configure(image=self.tk_image, text="")

    def show_progress(self):
        self.progress.pack(side="right", padx=10, pady=5)
        self.lbl_status.configure(text=f"Receiving: {self.incoming_file['name']}")

    def finish_file(self, name):
        self.progress.pack_forget()
        self.lbl_status.configure(text=f"Saved: {name}")

    def show_error(self, msg):
        self.lbl_status.configure(text=f"Error: {msg}")
        self.stop_connection()

    def toggle_fullscreen(self):
        self.full_screen = not self.full_screen
        self.attributes("-fullscreen", self.full_screen)
        if self.full_screen:
            self.controls_frame.grid_remove()
            self.status_bar.grid_remove()
            self.display_frame.configure(padx=0, pady=0)
            self.display_frame.grid(row=0, column=0, rowspan=3, sticky="nsew")
        else: 
            self.exit_fullscreen()

    def exit_fullscreen(self):
        self.full_screen = False
        self.attributes("-fullscreen", False)
        self.controls_frame.grid()
        self.status_bar.grid()
        self.display_frame.configure(padx=20, pady=(0, 10))
        self.display_frame.grid(row=1, column=0, sticky="nsew")
        self.btn_fullscreen.configure(text="Full Screen")

if __name__ == "__main__":
    app = WiFiMonitorClient()
    app.mainloop()
