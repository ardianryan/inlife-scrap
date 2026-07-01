from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import sqlite3
import os
import io
import threading
import time
import requests
from datetime import datetime
from db import init_db, save_applicant, get_applicants, get_positions, get_majors, get_stats, DB_PATH, get_setting, set_setting

# Initialize Flask app serving from static directory
app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Global dicts to manage real-time background threads status
sync_state = {
    "status": "idle",  # "idle", "running", "complete", "error"
    "current": 0,
    "total": 0,
    "logs": []
}

wa_blast_state = {
    "status": "idle",  # "idle", "sending", "complete", "error"
    "current": 0,
    "total": 0,
    "success_count": 0,
    "failed_count": 0,
    "logs": []
}

# --- STATIC ASSETS SERVER ---
@app.route('/')
def index():
    """Serves the main single page application template."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serves styles, scripts, images, and other resources."""
    return send_from_directory(app.static_folder, path)

# --- API ENDPOINTS ---

@app.route('/api/login', methods=['POST'])
def api_login():
    """Validates administrator credentials and returns session token."""
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    
    if username == "admin" and password == "admin1234567890":
        return jsonify({"status": "success", "token": "authenticated"})
    
    return jsonify({"status": "error", "message": "Invalid username or password"}), 401

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Calculates database stats, distribution breakdowns, and connections."""
    stats = get_stats()
    
    # Get last scraped timestamp
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT MAX(scraped_at) FROM applicants")
    last_scraped = c.fetchone()[0]
    conn.close()
    
    formatted_dt = "No records found"
    if last_scraped:
        try:
            dt = datetime.fromisoformat(last_scraped)
            formatted_dt = dt.strftime("%d %b %Y, %H:%M")
        except Exception:
            formatted_dt = last_scraped
            
    stats["last_updated"] = formatted_dt
    stats["db_size_kb"] = os.path.getsize(DB_PATH) / 1024 if os.path.exists(DB_PATH) else 0
    stats["unique_positions_count"] = len(stats.get("position_distribution", {}))
    return jsonify(stats)

@app.route('/api/filters', methods=['GET'])
def api_filters():
    """Returns lists of positions and majors to populate select dropdowns."""
    return jsonify({
        "positions": get_positions(),
        "majors": get_majors()
    })

@app.route('/api/applicants', methods=['GET'])
def api_applicants():
    """Queries, searches, and filters candidate database table."""
    search = request.args.get("search")
    position = request.args.get("position")
    major = request.args.get("major")
    
    db_pos = None if not position or position == "All Positions" else position
    db_major = None if not major or major == "All Majors" else major
    db_search = None if not search or search.strip() == "" else search
    
    applicants = get_applicants(search_query=db_search, position_filter=db_pos, major_filter=db_major)
    return jsonify(applicants)

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """Handles retrieval and update of credentials and WhatsApp GOWA configs."""
    default_template = (
        "Halo {{nama}},\n\n"
        "Selamat! Anda dinyatakan lolos seleksi berkas untuk posisi {{posisi}} di Inlife Surabaya.\n\n"
        "Harap membalas pesan ini untuk konfirmasi kehadiran sesi interview.\n\n"
        "Terima kasih."
    )
    
    if request.method == 'GET':
        email = get_setting("mentor_email", "newgen@gmail.com")
        password = get_setting("mentor_password", "Tapfya88")
        wa_api_url = get_setting("wa_api_url", "http://localhost:3000")
        wa_device_id = get_setting("wa_device_id", "default")
        wa_template = get_setting("wa_template", default_template)
        wa_test_phone = get_setting("wa_test_phone", "")
        
        return jsonify({
            "mentor_email": email,
            "mentor_password": password,
            "wa_api_url": wa_api_url,
            "wa_device_id": wa_device_id,
            "wa_template": wa_template,
            "wa_test_phone": wa_test_phone
        })
    
    # POST request
    data = request.json or {}
    email = data.get("mentor_email")
    password = data.get("mentor_password")
    wa_api_url = data.get("wa_api_url")
    wa_device_id = data.get("wa_device_id")
    wa_template = data.get("wa_template")
    wa_test_phone = data.get("wa_test_phone")
    
    if email:
        set_setting("mentor_email", email)
    if password:
        set_setting("mentor_password", password)
    if wa_api_url:
        set_setting("wa_api_url", wa_api_url)
    if wa_device_id:
        set_setting("wa_device_id", wa_device_id)
    if wa_template:
        set_setting("wa_template", wa_template)
    if wa_test_phone is not None:
        set_setting("wa_test_phone", wa_test_phone)
        
    return jsonify({"status": "success", "message": "Settings saved successfully"})

@app.route('/api/clear', methods=['POST'])
def api_clear():
    """Clears cached candidate records from the applicants table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM applicants")
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Database records cleared successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- BACKGROUND SCRAPING MANAGEMENT ---

def run_sync_thread(email, password):
    """Background worker thread to run scraper generator and update sync state."""
    global sync_state
    try:
        from scraper import scrape_generator
        sync_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing synchronization...")
        for event in scrape_generator(email, password):
            if event["type"] == "status":
                sync_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {event['message']}")
            elif event["type"] == "progress":
                sync_state["current"] = event["current"]
                sync_state["total"] = event["total"]
                sync_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {event['message']}")
            elif event["type"] == "complete":
                sync_state["status"] = "complete"
                sync_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {event['message']}")
                return
            elif event["type"] == "error":
                sync_state["status"] = "error"
                sync_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {event['message']}")
                return
    except Exception as e:
        sync_state["status"] = "error"
        sync_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] FATAL ERROR: {str(e)}")

@app.route('/api/sync', methods=['POST'])
def api_sync():
    """Triggers background scraping thread."""
    global sync_state
    if sync_state["status"] == "running":
        return jsonify({"status": "error", "message": "Sync is already running"}), 400
        
    email = get_setting("mentor_email", "newgen@gmail.com")
    password = get_setting("mentor_password", "Tapfya88")
    
    # Reset sync logs state
    sync_state["status"] = "running"
    sync_state["current"] = 0
    sync_state["total"] = 0
    sync_state["logs"] = []
    
    t = threading.Thread(target=run_sync_thread, args=(email, password))
    t.daemon = True
    t.start()
    
    return jsonify({"status": "success", "message": "Synchronization started"})

@app.route('/api/sync/status', methods=['GET'])
def api_sync_status():
    """Returns the current background scraping logs, counts, and status."""
    global sync_state
    return jsonify(sync_state)

# --- BACKGROUND WHATSAPP BLAST MANAGEMENT ---

def clean_phone_number(phone):
    """Sanitizes Indonesian phone numbers into standardized WhatsApp JID JID format."""
    if not phone:
        return None
    # Strip all non-digits
    cleaned = "".join(c for c in str(phone) if c.isdigit())
    if cleaned.startswith("0"):
        cleaned = "62" + cleaned[1:]
    if not cleaned.endswith("@s.whatsapp.net"):
        cleaned = cleaned + "@s.whatsapp.net"
    return cleaned

def run_wa_blast_thread(candidate_ids, template_msg, api_url, device_id):
    """Worker thread that formats messages and sends them to the local GOWA API."""
    global wa_blast_state
    try:
        wa_blast_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Memulai pengiriman blast WhatsApp ke {len(candidate_ids)} pelamar...")
        
        # Connect to SQLite
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        for idx, cid in enumerate(candidate_ids):
            wa_blast_state["current"] = idx + 1
            
            c.execute("SELECT name, position_title, university, phone_number FROM applicants WHERE id = ?", (cid,))
            row = c.fetchone()
            if not row:
                wa_blast_state["failed_count"] += 1
                wa_blast_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] GAGAL: Kandidat dengan ID {cid} tidak ditemukan di database.")
                continue
                
            name = row["name"]
            position = row["position_title"]
            university = row["university"]
            phone = row["phone_number"]
            
            # Format message template variables
            msg = template_msg
            msg = msg.replace("{{nama}}", name).replace("{{Nama}}", name)
            msg = msg.replace("{{posisi}}", position).replace("{{Posisi}}", position)
            msg = msg.replace("{{kampus}}", university).replace("{{Kampus}}", university).replace("{{universitas}}", university)
            
            # Clean JID phone format
            jid = clean_phone_number(phone)
            if not jid:
                wa_blast_state["failed_count"] += 1
                wa_blast_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] GAGAL: Nomor telepon pelamar {name} kosong.")
                continue
                
            # Endpoint GOWA
            url = f"{api_url.rstrip('/')}/send/message"
            headers = {"Content-Type": "application/json"}
            if device_id and device_id.strip() != "":
                headers["X-Device-Id"] = device_id
                
            payload = {
                "phone": jid,
                "message": msg
            }
            
            try:
                # Trigger call to GOWA
                res = requests.post(url, json=payload, headers=headers, timeout=7)
                if res.status_code in [200, 201]:
                    wa_blast_state["success_count"] += 1
                    wa_blast_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] BERHASIL: Pesan dikirim ke {name} ({phone})")
                else:
                    wa_blast_state["failed_count"] += 1
                    wa_blast_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] GAGAL: {name} ({phone}) - HTTP {res.status_code}: {res.text}")
            except Exception as err:
                wa_blast_state["failed_count"] += 1
                wa_blast_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] GAGAL: {name} ({phone}) - Error koneksi: {str(err)}")
                
            # Jeda minimal 5 detik untuk menghindari deteksi spam / blokir
            time.sleep(5)
            
        conn.close()
        wa_blast_state["status"] = "complete"
        wa_blast_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Broadcast selesai! Terkirim: {wa_blast_state['success_count']}, Gagal: {wa_blast_state['failed_count']}.")
        
    except Exception as e:
        wa_blast_state["status"] = "error"
        wa_blast_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] FATAL ERROR: {str(e)}")

@app.route('/api/wa/blast', methods=['POST'])
def api_wa_blast():
    """Triggers background WhatsApp broadcast thread."""
    global wa_blast_state
    if wa_blast_state["status"] == "sending":
        return jsonify({"status": "error", "message": "WhatsApp blast is already running"}), 400
        
    data = request.json or {}
    candidate_ids = data.get("candidate_ids", [])
    template_msg = data.get("message_template", "")
    
    if not candidate_ids:
        return jsonify({"status": "error", "message": "No candidates selected"}), 400
    if not template_msg:
        return jsonify({"status": "error", "message": "Message template is empty"}), 400
        
    api_url = get_setting("wa_api_url", "http://localhost:3000")
    device_id = get_setting("wa_device_id", "default")
    
    # Reset state
    wa_blast_state["status"] = "sending"
    wa_blast_state["current"] = 0
    wa_blast_state["total"] = len(candidate_ids)
    wa_blast_state["success_count"] = 0
    wa_blast_state["failed_count"] = 0
    wa_blast_state["logs"] = []
    
    # Run in background
    t = threading.Thread(target=run_wa_blast_thread, args=(candidate_ids, template_msg, api_url, device_id))
    t.daemon = True
    t.start()
    
    return jsonify({"status": "success", "message": "WhatsApp blast initiated"})

@app.route('/api/wa/blast/status', methods=['GET'])
def api_wa_blast_status():
    """Returns the current background WhatsApp blast progress logs and counts."""
    global wa_blast_state
    return jsonify(wa_blast_state)

@app.route('/api/wa/test', methods=['POST'])
def api_wa_test():
    """Sends a single test WhatsApp message with dummy candidate variables."""
    data = request.json or {}
    phone = data.get("phone")
    api_url = data.get("wa_api_url")
    device_id = data.get("wa_device_id")
    template_msg = data.get("message_template", "")
    
    if not phone:
        return jsonify({"status": "error", "message": "Test recipient phone number is required"}), 400
    if not api_url:
        return jsonify({"status": "error", "message": "GOWA API Base URL is required"}), 400
        
    jid = clean_phone_number(phone)
    if not jid:
        return jsonify({"status": "error", "message": "Invalid phone number format"}), 400
        
    # Compile mock message
    msg = template_msg
    msg = msg.replace("{{nama}}", "Budi Santoso").replace("{{Nama}}", "Budi Santoso")
    msg = msg.replace("{{posisi}}", "Software Engineer").replace("{{Posisi}}", "Software Engineer")
    msg = msg.replace("{{kampus}}", "Universitas Brawijaya").replace("{{Kampus}}", "Universitas Brawijaya")
    
    url = f"{api_url.rstrip('/')}/send/message"
    headers = {"Content-Type": "application/json"}
    if device_id and device_id.strip() != "":
        headers["X-Device-Id"] = device_id
        
    payload = {
        "phone": jid,
        "message": msg
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            return jsonify({"status": "success", "message": f"Test message sent successfully to {jid}"})
        else:
            return jsonify({"status": "error", "message": f"HTTP {res.status_code}: {res.text}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to connect to GOWA server: {str(e)}"}), 500

# --- EXPORTS ---

@app.route('/api/export', methods=['GET'])
def api_export():
    """Generates and downloads Excel matching current active filters."""
    search = request.args.get("search")
    position = request.args.get("position")
    major = request.args.get("major")
    
    db_pos = None if not position or position == "All Positions" else position
    db_major = None if not major or major == "All Majors" else major
    db_search = None if not search or search.strip() == "" else search
    
    applicants = get_applicants(search_query=db_search, position_filter=db_pos, major_filter=db_major)
    df = pd.DataFrame(applicants)
    
    if df.empty:
        return "No candidate data matched criteria", 400
        
    export_df = df[["name", "phone_number", "email"]].copy()
    export_df.rename(columns={
        "name": "Nama",
        "phone_number": "Nomor WA/HP",
        "email": "Email"
    }, inplace=True)
    
    export_df.index = range(1, len(export_df) + 1)
    export_df.index.name = "No"
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name='Data Pelamar Magang')
        workbook = writer.book
        worksheet = writer.sheets['Data Pelamar Magang']
        
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 10)
            
    buffer.seek(0)
    
    safe_pos = (position or "all").lower().replace(' ', '_')
    filename = f"candidates_{safe_pos}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    # Initialize DB schema
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='127.0.0.1', port=port, debug=False)
