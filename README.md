# Internship Scraper Console

[Indonesian]  
Aplikasi pencatat, penarik, dan manajemen data pelamar magang secara otomatis dari portal mentor Inlife. Menggunakan basis Single Page Application (SPA) HTML/JS/CSS yang cepat, dengan backend Python Flask lokal, WhatsApp blast dengan skema Round-Robin, dan database SQLite.

[English]  
An automated candidate logging, scraping, and management application for the Inlife mentor portal. Built as a fast HTML/JS/CSS Single Page Application (SPA) with a local Python Flask backend, Round-Robin WhatsApp broadcasting engine, and SQLite database caching.

---

## 🌟 Key Features / Fitur Utama

- **Automated Scraping / Penarikan Otomatis**: Natively fetches candidate applications directly from the Inlife mentor portal.
- **SQLite Database Cache / Penyimpanan Lokal**: Stores candidate details locally for rapid searching, filtering, and offline access.
- **WhatsApp Round-Robin Broadcast / Blast WA Bergantian**: Rotates outgoing messages through multiple WhatsApp accounts to distribute load and prevent phone numbers from being banned.
- **Native Device Connection / Penautan WA Native**: Link new WhatsApp accounts directly inside the dashboard using either **QR Code** scanning or 8-digit **Pairing Code** entry.
- **Auto-Boot WhatsApp Engine / Pemuatan GOWA Otomatis**: The backend automatically detects your operating system, downloads the correct GOWA engine binary, and manages its background lifecycle.
- **Desktop & Web Modes / Jendela Desktop & Web**: Launch as a standalone native desktop application or run as a local web server.

---

## 📋 Prerequisites / Persyaratan Awal

- **Python 3.9** or higher / atau lebih tinggi.
- **Windows Users**: Check the option **"Add Python to PATH"** during Python installation.
- **Pengguna Windows**: Pastikan mencentang kotak **"Add Python to PATH"** saat proses instalasi dimulai.

---

## 🚀 One-Click Quick Start / Cara Menjalankan Instan

The application includes automated scripts that verify Python, create a virtual environment, install required packages (`requirements.txt`), download GOWA, and launch the console.

Aplikasi ini dilengkapi dengan skrip otomatis yang akan memverifikasi Python, membuat Virtual Environment, menginstal dependensi (`requirements.txt`), mengunduh GOWA, dan langsung membuka antarmuka dasbor.

### 🍎 macOS / Linux
1. Open **Terminal** / Buka aplikasi **Terminal**.
2. Navigate to this project folder and run / Masuk ke folder proyek ini dan jalankan:
   ```bash
   chmod +x run.sh && ./run.sh
   ```

### 💻 Windows
1. Open this project folder in **File Explorer** / Buka folder proyek ini di **File Explorer**.
2. Double-click the file named / Klik ganda pada berkas bernama:
   **`run.bat`**

---

## 🛠️ Manual Execution (Dev / Debug) / Cara Menjalankan Manual

If you want to run the application manually step-by-step for debugging or development:

Jika Anda ingin menjalankan aplikasi secara manual langkah-demi-langkah (misal untuk keperluan pengembangan/debug):

### 1. Navigate to Project Directory / Masuk ke Direktori Proyek
```bash
cd /path/to/folder/scrapinginlife
```

### 2. Set Up Virtual Environment / Buat & Aktifkan Virtual Environment
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

### 3. Install Dependencies / Instal Seluruh Dependensi
```bash
pip install -r requirements.txt
```

### 4. Run Application / Jalankan Aplikasi
Choose one of the execution modes below / Pilih salah satu mode eksekusi di bawah:

* **Web Browser Mode (Flask Backend Only)**:
  ```bash
  # macOS/Linux:
  python3 app.py
  # Windows:
  python app.py
  ```
  Open your web browser and navigate to / Buka peramban web Anda dan buka:  
  👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

* **Native Desktop Mode (Webview Window)**:
  ```bash
  # macOS/Linux:
  python3 desktop.py
  # Windows:
  python desktop.py
  ```
  Launches a standalone native application window / Membuka jendela aplikasi desktop lokal mandiri.

---

## 🔒 Login Credentials / Informasi Akses Dasbor

### Default Credentials / Kredensial Login Default
* **Username**: `admin`
* **Password**: `admin1234567890`
