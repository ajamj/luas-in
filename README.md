# luas-in

`luas-in` adalah solusi *open-source* untuk memperluas layar laptop Windows ke perangkat Linux dan Android dalam jaringan lokal (LAN) dengan performa tinggi. Proyek ini menggunakan arsitektur modular dengan RTSP/H.264 untuk latensi rendah.

## 🚀 Fitur Utama
- **Video Streaming**: Menggunakan RTSP/H.264 dengan akselerasi perangkat keras via PyAV (FFmpeg).
- **Client Cross-Platform**: Aplikasi client berbasis Flet (Flutter) yang mendukung Linux dan Android.
- **Input Forwarding**: Mouse dan keyboard pada client dapat mengontrol host Windows (server).
- **Modular Core**: Logika networking terpusat pada `luasin_core.py`.

## 🛠️ Instalasi

### Prasyarat
- Python 3.10+
- Host (Windows): `customtkinter`, `mss`, `Pillow`, `pyperclip`, `av`, `pynput`
- Client (Linux/Android): `flet`, `av`

### Setup
1. Clone repository:
   ```bash
   git clone <url-repo>
   cd luas-in
   ```
2. Instal dependensi server (Windows):
   ```bash
   pip install customtkinter mss Pillow pyperclip av pynput
   ```
3. Instal dependensi client (Linux/Android):
   ```bash
   pip install flet av
   ```

## 📖 Penggunaan

### Server (Windows)
1. Jalankan `python server.py`.
2. Masukkan Port dan Password, lalu klik **Start Server**.
3. Pastikan host terhubung ke jaringan lokal yang sama dengan client.

### Client (Linux/Android)
1. Jalankan `python client_flet.py`.
2. Masukkan alamat IP Server, port, dan password.
3. Klik **Connect** untuk memulai streaming.

## 🏗️ Arsitektur

### Komponen
- `luasin_core.py`: Pustaka inti yang menangani networking, otentikasi, dan RTSP streaming.
- `server.py`: Antarmuka server Windows berbasis CustomTkinter.
- `client_flet.py`: Antarmuka client lintas platform berbasis Flet.

## ⚖️ Lisensi
MIT
