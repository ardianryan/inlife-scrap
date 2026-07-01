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

def start_flask(port):
    """Menjalankan server Flask di subprocess latar belakang."""
    # Deteksi lokasi executable python saat ini
    python_bin = sys.executable
    
    # Argumen untuk menjalankan app.py (Flask)
    args = [python_bin, "app.py"]
    
    # Copy env vars dan set port untuk Flask
    env = os.environ.copy()
    env["PORT"] = str(port)
    
    # Jalankan subprocess dan kembalikan referensi prosesnya
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

if __name__ == '__main__':
    # 1. Cari port dinamis yang kosong
    port = find_free_port()
    
    # 2. Jalankan Flask server
    process = start_flask(port)
    
    # 3. Beri jeda 2 detik agar Flask server siap memuat halaman
    time.sleep(2)
    
    try:
        # 4. Buat dan buka jendela aplikasi desktop mandiri
        webview.create_window(
            title='Internship Scraper Console', 
            url=f'http://127.0.0.1:{port}/?session=authenticated',
            width=1280, 
            height=800,
            resizable=True
        )
        
        # Mulai UI window desktop (akan memblokir eksekusi di sini hingga jendela ditutup)
        webview.start()
        
    finally:
        # Bagian ini AKAN SELALU dijalankan saat jendela aplikasi desktop ditutup
        print("Menghentikan server Flask di latar belakang...")
        if process:
            try:
                # Kirim sinyal pemberhentian ke subprocess Flask
                process.terminate()
                # Tunggu maksimal 2 detik untuk keluar secara rapi
                process.wait(timeout=2)
            except Exception:
                try:
                    # Paksa matikan jika terminate gagal/tergantung
                    process.kill()
                except Exception:
                    pass
            print("Server Flask berhasil dihentikan.")
