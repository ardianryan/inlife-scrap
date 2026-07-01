# Internship Scraper Console

Aplikasi pencatat, penarik, dan manajemen data pelamar magang secara otomatis dari portal mentor Inlife. Menggunakan basis Single Page Application (SPA) HTML/JS/CSS yang cepat, dengan backend Python Flask lokal dan database SQLite.

## Persyaratan Awal
Pastikan komputer Anda sudah terpasang **Python 3**. Jika belum, silakan unduh dan pasang dari [python.org](https://www.python.org/downloads/).
> **Khusus Windows**: Pastikan mencentang kotak **"Add Python to PATH"** saat proses instalasi dimulai.

---

## 🚀 Cara Menjalankan Instan (Satu-Klik)

Aplikasi ini dilengkapi dengan skrip otomatis yang akan memverifikasi Python, membuat Virtual Environment, menginstal pustaka yang dibutuhkan (`requirements.txt`), dan langsung membuka antarmuka dasbor.

### 🍎 Pengguna macOS / Linux
1. Buka aplikasi **Terminal**.
2. Jalankan perintah berikut:
   ```bash
   ./run.sh
   ```

### 💻 Pengguna Windows
1. Buka folder proyek ini di **File Explorer**.
2. Klik ganda (double-click) pada berkas bernama:
   **`run.bat`**

---

## 🛠️ Cara Menjalankan Secara Manual (Development / Server Mode)

Jika Anda ingin menjalankan aplikasi secara manual langkah-demi-langkah (misal untuk keperluan pengembangan/debug):

### 1. Masuk ke Direktori Proyek
```bash
cd /path/to/folder/scrapinginlife
```

### 2. Buat & Aktifkan Virtual Environment
* **macOS / Linux**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
* **Windows**:
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate
  ```

### 3. Instal Seluruh Dependensi
```bash
pip install -r requirements.txt
```

### 4. Jalankan Aplikasi
Terdapat dua mode eksekusi yang bisa Anda pilih:

* **Mode Peramban Web (Flask Server Only)**:
  ```bash
  # Di macOS/Linux:
  python3 app.py
  # Atau jalankan lewat venv:
  .venv/bin/python app.py
  ```
  Aplikasi akan berjalan sebagai server backend. Anda dapat membukanya melalui browser di:
  👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

* **Mode Aplikasi Desktop Native (Webview Wrapper)**:
  ```bash
  # Di macOS/Linux:
  python3 desktop.py
  # Atau jalankan lewat venv:
  .venv/bin/python desktop.py
  ```
  Aplikasi akan otomatis memicu jendela aplikasi desktop macOS/Windows mandiri secara lokal (port Flask akan dideteksi secara otomatis dan dibersihkan ketika jendela ditutup).

---

## 🔒 Informasi Akses Dasbor

### Kredensial Login Default
* **Username**: `admin`
* **Password**: `admin1234567890`
