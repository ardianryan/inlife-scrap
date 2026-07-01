import subprocess
import time
import webview
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
    
    # Jalankan subprocess dan kembalikan referensi prosesnya
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == '__main__':
    # 1. Cari port dinamis yang kosong
    port = find_free_port()
    
    # 2. Jalankan Streamlit server
    process = start_streamlit(port)
    
    # 3. Beri jeda 3 detik agar server Streamlit siap memuat halaman
    time.sleep(3)
    
    try:
        # 4. Buat dan buka jendela aplikasi desktop mandiri
        webview.create_window(
            title='Internship Scraper Console', 
            url=f'http://localhost:{port}/?session=authenticated',
            width=1280, 
            height=800,
            resizable=True
        )
        
        # Mulai UI window desktop (akan memblokir eksekusi di sini hingga jendela ditutup)
        webview.start()
        
    finally:
        # Bagian ini AKAN SELALU dijalankan saat jendela aplikasi desktop ditutup
        print("Menghentikan server Streamlit di latar belakang...")
        if process:
            try:
                # Kirim sinyal pemberhentian ke subprocess
                process.terminate()
                # Tunggu maksimal 2 detik untuk keluar secara rapi
                process.wait(timeout=2)
            except Exception:
                try:
                    # Paksa matikan jika terminate gagal/tergantung
                    process.kill()
                except Exception:
                    pass
            print("Server Streamlit berhasil dihentikan.")
