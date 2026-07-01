import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "interns.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applicants (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        position_id INTEGER,
        status TEXT,
        tahap TEXT,
        kk_url TEXT,
        pengantar_url TEXT,
        nama_kontak_darurat TEXT,
        hubungan_kontak_darurat TEXT,
        phone_kontak_darurat TEXT,
        day_interview TEXT,
        time_interview TEXT,
        location_interview TEXT,
        note_interview TEXT,
        day_onboarding TEXT,
        time_onboarding TEXT,
        location_onboarding TEXT,
        pesan_mentor TEXT,
        note_onboarding TEXT,
        nda_url TEXT,
        loa_url TEXT,
        
        -- User profile details
        name TEXT,
        email TEXT,
        phone_number TEXT,
        address TEXT,
        birth_date TEXT,
        avatar_url TEXT,
        birth_place TEXT,
        education_level TEXT,
        university TEXT,
        faculty TEXT,
        major TEXT,
        nim TEXT,
        ipk TEXT,
        graduation_status TEXT,
        graduation_period TEXT,
        gender TEXT,
        hobby TEXT,
        ktp_url TEXT,
        instagram TEXT,
        linkedin TEXT,
        
        -- Nested arrays stored as JSON strings
        organizations TEXT,
        experiences TEXT,
        projects TEXT,
        hard_skills TEXT,
        soft_skills TEXT,
        
        -- Position details
        position_title TEXT,
        position_location TEXT,
        position_duration INTEGER,
        position_type TEXT,
        position_description TEXT,
        
        scraped_at TEXT
    )
    """)
    
    # Create settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # Seed default values if not exists
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('mentor_email', 'newgen@gmail.com')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('mentor_password', 'Tapfya88')")
    
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    """
    Retrieves a configuration value from settings.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["value"]
    return default

def set_setting(key, value):
    """
    Saves or updates a configuration value.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def save_applicant(app_data):
    """
    Saves or updates an applicant detailed dictionary retrieved from the API.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Helper to serialize complex items
    def to_json_str(val):
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return str(val)

    user = app_data.get("user", {}) or {}
    position = app_data.get("position", {}) or {}
    
    # Extract values
    val_map = {
        "id": app_data.get("id"),
        "user_id": app_data.get("user_id"),
        "position_id": app_data.get("position_id"),
        "status": app_data.get("status"),
        "tahap": app_data.get("tahap"),
        "kk_url": app_data.get("kk_url"),
        "pengantar_url": app_data.get("pengantar_url"),
        "nama_kontak_darurat": app_data.get("nama_kontak_darurat"),
        "hubungan_kontak_darurat": app_data.get("hubungan_kontak_darurat"),
        "phone_kontak_darurat": app_data.get("phone_kontak_darurat"),
        "day_interview": app_data.get("day_interview"),
        "time_interview": app_data.get("time_interview"),
        "location_interview": app_data.get("location_interview"),
        "note_interview": app_data.get("note_interview"),
        "day_onboarding": app_data.get("day_onboarding"),
        "time_onboarding": app_data.get("time_onboarding"),
        "location_onboarding": app_data.get("location_onboarding"),
        "pesan_mentor": app_data.get("pesan_mentor"),
        "note_onboarding": app_data.get("note_onboarding"),
        "nda_url": app_data.get("nda_url"),
        "loa_url": app_data.get("loa_url"),
        
        # User details
        "name": user.get("name"),
        "email": user.get("email"),
        "phone_number": user.get("phone_number"),
        "address": user.get("address"),
        "birth_date": user.get("birth_date"),
        "avatar_url": user.get("avatar_url"),
        "birth_place": user.get("birth_place"),
        "education_level": user.get("education_level"),
        "university": user.get("university"),
        "faculty": user.get("faculty"),
        "major": user.get("major"),
        "nim": user.get("nim"),
        "ipk": user.get("ipk"),
        "graduation_status": user.get("graduation_status"),
        "graduation_period": user.get("graduation_period"),
        "gender": user.get("gender"),
        "hobby": user.get("hobby"),
        "ktp_url": user.get("ktp_url"),
        "instagram": user.get("instagram"),
        "linkedin": user.get("linkedin"),
        
        # Arrays / JSON
        "organizations": to_json_str(user.get("organizations")),
        "experiences": to_json_str(user.get("experiences")),
        "projects": to_json_str(user.get("projects")),
        "hard_skills": to_json_str(user.get("hard_skills")),
        "soft_skills": to_json_str(user.get("soft_skills")),
        
        # Position details
        "position_title": position.get("title"),
        "position_location": position.get("location"),
        "position_duration": position.get("duration"),
        "position_type": position.get("type"),
        "position_description": position.get("description"),
        
        # Metadata
        "scraped_at": datetime.now().isoformat()
    }
    
    # Check if applicant already exists
    cursor.execute("SELECT id FROM applicants WHERE id = ?", (val_map["id"],))
    exists = cursor.fetchone()
    
    if exists:
        # Update
        update_cols = []
        params = []
        for col, val in val_map.items():
            if col != "id":
                update_cols.append(f"{col} = ?")
                params.append(val)
        params.append(val_map["id"])
        query = f"UPDATE applicants SET {', '.join(update_cols)} WHERE id = ?"
        cursor.execute(query, params)
    else:
        # Insert
        cols = list(val_map.keys())
        placeholders = ", ".join(["?"] * len(cols))
        params = [val_map[c] for c in cols]
        query = f"INSERT INTO applicants ({', '.join(cols)}) VALUES ({placeholders})"
        cursor.execute(query, params)
        
    conn.commit()
    conn.close()

def get_positions():
    """
    Returns list of unique positions in database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT position_title FROM applicants WHERE position_title IS NOT NULL ORDER BY position_title")
    rows = cursor.fetchall()
    positions = [row["position_title"] for row in rows]
    conn.close()
    return positions

def get_majors():
    """
    Returns list of unique majors (program studi) in database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT major FROM applicants WHERE major IS NOT NULL AND major != '' ORDER BY major")
    rows = cursor.fetchall()
    majors = [row["major"] for row in rows]
    conn.close()
    return majors

def get_applicants(search_query=None, position_filter=None, major_filter=None):
    """
    Query applicants based on filters. Returns list of dicts.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM applicants WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (name LIKE ? OR email LIKE ? OR university LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])
        
    if position_filter:
        query += " AND position_title = ?"
        params.append(position_filter)
        
    if major_filter:
        query += " AND major = ?"
        params.append(major_filter)
        
    query += " ORDER BY name ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convert sqlite3.Row to dict
    applicants = [dict(row) for row in rows]
    conn.close()
    return applicants

def get_stats():
    """
    Get summary statistics from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total applicants
    cursor.execute("SELECT COUNT(*) FROM applicants")
    stats["total"] = cursor.fetchone()[0]
    
    # Systems Information count
    cursor.execute("SELECT COUNT(*) FROM applicants WHERE UPPER(major) = 'SISTEM INFORMASI'")
    stats["total_si"] = cursor.fetchone()[0]
    
    # Stages distribution
    cursor.execute("SELECT tahap, COUNT(*) FROM applicants GROUP BY tahap")
    stats["tahap_distribution"] = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Positions distribution
    cursor.execute("SELECT position_title, COUNT(*) FROM applicants GROUP BY position_title")
    stats["position_distribution"] = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    return stats
