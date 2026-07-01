import subprocess
import time
import webview
import sys
import socket
import os
import sqlite3
import pandas as pd
from datetime import datetime
from db import get_applicants

def find_free_port():
    """Mencari port kosong yang tersedia di komputer secara dinamis."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def start_flask(port):
    """Menjalankan server Flask di subprocess latar belakang."""
    python_bin = sys.executable
    args = [python_bin, "app.py"]
    env = os.environ.copy()
    env["PORT"] = str(port)
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

class DesktopApi:
    """API Bridge yang diekspos ke konteks Javascript di dalam PyWebview."""
    def __init__(self):
        self.window = None

    def set_window(self, window):
        self.window = window

    def download_excel(self, search, position, major):
        """Membuka dialog simpan berkas native OS dan menulis file Excel secara langsung."""
        if not self.window:
            return {"status": "error", "message": "Desktop window not initialized"}

        try:
            # 1. Tampilkan Dialog Simpan File Native OS (Save As...)
            file_path = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=os.path.expanduser('~'),
                save_filename=f"candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                file_types=('Excel Files (*.xlsx)', 'All Files (*.*)')
            )
            
            if not file_path:
                return {"status": "cancelled"}  # Pengguna membatalkan dialog

            # Handle format return dialog (beberapa OS mengembalikan tuple/list)
            if isinstance(file_path, (list, tuple)):
                if len(file_path) > 0:
                    file_path = file_path[0]
                else:
                    return {"status": "cancelled"}

            # 2. Tarik data dari SQLite database lokal secara langsung
            db_pos = None if not position or position == "All Positions" else position
            db_major = None if not major or major == "All Majors" else major
            db_search = None if not search or search.strip() == "" else search
            
            applicants = get_applicants(search_query=db_search, position_filter=db_pos, major_filter=db_major)
            df = pd.DataFrame(applicants)
            
            if df.empty:
                return {"status": "error", "message": "No candidate data matched criteria"}

            # 3. Format DataFrame
            export_df = df[["name", "phone_number", "email"]].copy()
            export_df.rename(columns={
                "name": "Nama",
                "phone_number": "Nomor WA/HP",
                "email": "Email"
            }, inplace=True)
            export_df.index = range(1, len(export_df) + 1)
            export_df.index.name = "No"

            # 4. Tulis file Excel langsung ke jalur yang dipilih pengguna
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                export_df.to_excel(writer, sheet_name='Data Pelamar Magang')
                worksheet = writer.sheets['Data Pelamar Magang']
                
                # Auto-adjust kolom
                for col in worksheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = col[0].column_letter
                    worksheet.column_dimensions[col_letter].width = max(max_len + 3, 10)

            return {"status": "success", "path": file_path}

        except Exception as e:
            return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    # 1. Cari port dinamis yang kosong
    port = find_free_port()
    
    # 2. Jalankan Flask server
    process = start_flask(port)
    
    # 3. Jeda agar Flask siap
    time.sleep(2)
    
    api = DesktopApi()
    
    try:
        # 4. Buat dan buka jendela aplikasi desktop mandiri dengan JS API Bridge
        window = webview.create_window(
            title='Internship Scraper Console', 
            url=f'http://127.0.0.1:{port}/?session=authenticated',
            width=1280, 
            height=800,
            resizable=True,
            js_api=api
        )
        api.set_window(window)
        
        # Mulai UI window desktop (memblokir eksekusi di sini hingga jendela ditutup)
        webview.start()
        
    finally:
        # Bagian ini AKAN SELALU dijalankan saat jendela aplikasi desktop ditutup
        print("Menghentikan server Flask di latar belakang...")
        if process:
            try:
                process.terminate()
                process.wait(timeout=2)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
            print("Server Flask berhasil dihentikan.")
