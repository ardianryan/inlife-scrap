from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import sqlite3
import os
import io
import threading
import pandas as pd
from datetime import datetime
from db import init_db, save_applicant, get_applicants, get_positions, get_majors, get_stats, DB_PATH, get_setting, set_setting
from scraper import scrape_generator

# Initialize Flask app serving from static directory
app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes (useful for Webview wrapper calls)

# Global dictionary to manage real-time scraper thread status
sync_state = {
    "status": "idle",  # "idle", "running", "complete", "error"
    "current": 0,
    "total": 0,
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
    """Handles retrieval and update of Inlife mentor credentials in SQLite settings."""
    if request.method == 'GET':
        email = get_setting("mentor_email", "newgen@gmail.com")
        password = get_setting("mentor_password", "Tapfya88")
        return jsonify({"mentor_email": email, "mentor_password": password})
    
    # POST request
    data = request.json or {}
    email = data.get("mentor_email")
    password = data.get("mentor_password")
    
    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password cannot be empty"}), 400
        
    set_setting("mentor_email", email)
    set_setting("mentor_password", password)
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
    
    # Fire thread
    t = threading.Thread(target=run_sync_thread, args=(email, password))
    t.daemon = True
    t.start()
    
    return jsonify({"status": "success", "message": "Synchronization started"})

@app.route('/api/sync/status', methods=['GET'])
def api_sync_status():
    """Returns the current background scraping logs, counts, and status."""
    global sync_state
    return jsonify(sync_state)

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
