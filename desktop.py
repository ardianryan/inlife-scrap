import subprocess
import time
import webview
import threading
import sys
import socket
import os

def find_free_port():
    """Mencari port kosong yang tersedia di komputer secara dinamis."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def start_streamlit(port):
    """Menjalankan server Streamlit di subprocess latar belakang (headless)."""
    # Deteksi lokasi executable python saat ini
    python_bin = sys.executable
    
    # Argumen untuk Streamlit
    args = [
        python_bin, "-m", "streamlit", "run", "app.py",
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    # Jalankan subprocess
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == '__main__':
    # 1. Cari port dinamis yang kosong
    port = find_free_port()
    
    # 2. Jalankan Streamlit server di thread latar belakang
    t = threading.Thread(target=start_streamlit, args=(port,))
    t.daemon = True
    t.start()
    
    # 3. Beri jeda 3 detik agar server Streamlit siap memuat halaman
    time.sleep(3)
    
    # 4. Buat dan buka jendela aplikasi desktop mandiri pointing ke localhost
    # session=authenticated ditambahkan agar otomatis terhubung jika sesi tersimpan
    webview.create_window(
        title='Internship Scraper Console', 
        url=f'http://localhost:{port}/?session=authenticated',
        width=1280, 
        height=800,
        resizable=True
    )
    
    # Mulai UI window desktop
    webview.start()
