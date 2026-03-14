# WiFiMonitor Pro

WiFiMonitor Pro is a powerful, low-latency screen-sharing and productivity tool designed for Windows hosts and cross-platform clients. It turns your client device into a versatile extension of your workstation.

## 🚀 Features

- **Screen Sharing**: High-performance (30 FPS) screen capture and broadcasting.
- **Extended Display Mode**: Select specific monitors to share, allowing you to use your client as an external display.
- **Clipboard Sync**: Automatic, real-time clipboard synchronization between server and client.
- **File Transfer**: Send files from the server to all connected clients with progress tracking.
- **Immersive Fullscreen**: Truly borderless viewing mode (F11) on the client side.
- **Modern UI**: Built with CustomTkinter for a premium dark-themed experience.

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- OS: Windows (Server), Any (Client)

### Setup
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd luas-in
   ```
2. Install dependencies:
   ```bash
   pip install customtkinter mss Pillow pyperclip
   ```

## 📖 Usage

### Server (Windows)
1. Run `python server.py`.
2. Configure the **Port** and **Password**.
3. Select the **Target Monitor** if you have multiple displays.
4. Click **Start Server**.
5. Use the **Send File** button to broadcast files or copy text to share it via the clipboard.

### How to use Extended Mode (Monitor Eksternal)
Agar Client bisa menjadi monitor kedua yang terpisah (Extended Mode), Windows harus "melihat" adanya monitor kedua di sisi Server.
- **Opsi A (Fisik)**: Colokkan monitor fisik atau dummy HDMI plug ke Laptop Server.
- **Opsi B (Virtual - Rekomendasi)**: Gunakan driver monitor virtual seperti [IddSampleDriver](https://github.com/roshkins/IddSampleDriver/releases) atau [usbmmIdd](https://www.amyuni.com/forum/viewtopic.php?t=3030).
  1. Install driver tersebut di Windows Server.
  2. Tekan `Win + P` di keyboard, pilih **Extend**.
  3. Buka WiFiMonitor Server, pilih **Monitor 1** (atau Monitor 2 yang baru muncul).
  4. Jalankan Client, maka Client akan menampilkan desktop kedua Anda.

### Client
1. Run `python client.py`.
2. Enter the Server's IP Address, Port, and Password.
3. Click **Connect**.
4. Press **F11** for immersive fullscreen mode.
5. Received files will be saved in the `downloads/` folder.

## 📁 Project Structure
- `server.py`: The Windows host application.
- `client.py`: The cross-platform viewer application.
- `.gitignore`: Files to be ignored by Git.
- `downloads/`: Default folder for received files on the client side.

## ⚖️ License
MIT
