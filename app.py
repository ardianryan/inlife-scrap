import streamlit as st
import pandas as pd
import io
import os
import sqlite3
from datetime import datetime
from db import init_db, save_applicant, get_applicants, get_positions, get_majors, get_stats, DB_PATH, get_setting, set_setting
from scraper import scrape_generator

# Page Config
st.set_page_config(
    page_title="Internship Scraper Console",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
init_db()

# --- SESSION & COOKIE PERSISTENCE ---
if "authenticated" not in st.session_state:
    if st.query_params.get("session") == "authenticated":
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False

# Read page selection from URL query parameters (routing)
query_page = st.query_params.get("page", "Dashboard")
if query_page in ["Dashboard", "Sync", "Settings"]:
    st.session_state.current_page = query_page
else:
    st.session_state.current_page = "Dashboard"

# Render Login Page if not authenticated
if not st.session_state.authenticated:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
        
        /* Force light theme globally */
        .stApp {
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }
        
        /* Input overrides */
        div[data-baseweb="input"] {
            background-color: #ffffff !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
            border-radius: 6px !important;
        }
        input {
            color: #0f172a !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }
        
        /* Primary Login Button styling - Professional deep blue */
        .stButton>button {
            border-radius: 6px !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            background: #0f172a !important;
            color: white !important;
            border: 1px solid #0f172a !important;
            padding: 10px 20px !important;
            transition: all 0.2s ease !important;
        }
        .stButton>button:hover {
            background: #1e293b !important;
            border-color: #1e293b !important;
            transform: translateY(-1px) !important;
        }
        
        /* Center container style */
        .login-shell {
            background: #ffffff;
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 12px;
            padding: 45px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
            margin-top: 20px;
        }
        
        .material-icons {
            font-family: 'Material Icons' !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
        with st.container(border=False):
            st.markdown("""
            <div class="login-shell">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="display: inline-flex; align-items: center; justify-content: center; background: rgba(15, 23, 42, 0.05); border-radius: 50%; width: 50px; height: 50px; margin-bottom: 15px;">
                        <span class="material-icons" style="font-size: 24px; color: #0f172a;">lock</span>
                    </div>
                    <h2 style="font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 800; color: #0f172a; margin: 0; line-height: 1.1; letter-spacing: -0.5px;">
                        Scraper Console
                    </h2>
                    <p style="color: #475569; font-size: 0.9rem; margin-top: 8px; margin-bottom: 0;">Sign in to access the administrator panel.</p>
                </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("Username", value="admin", placeholder="Username admin...")
            password = st.text_input("Password", type="password", value="admin1234567890", placeholder="••••••••••••")
            
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            login_btn = st.button("Sign In", use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True) # close login-shell
            
            if login_btn:
                if username == "admin" and password == "admin1234567890":
                    st.session_state.authenticated = True
                    st.query_params["session"] = "authenticated"
                    st.query_params["page"] = "Dashboard"
                    st.success("Access granted.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.75rem; margin-top: 20px;'>Internship Scraper v1.4.0</div>", unsafe_allow_html=True)
    st.stop()

# --- BACKEND DASHBOARD (AUTHENTICATED) ---

# Custom CSS for Premium UI (Light Mode Edition with Material Icons)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    
    /* Force light theme globally */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
    .material-icons {
        font-family: 'Material Icons' !important;
    }
    
    /* Sidebar premium light redesign */
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #334155 !important;
    }
    
    /* HTML Sidebar Navigation Links */
    .sidebar-nav {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    .nav-item {
        display: flex;
        align-items: center;
        padding: 10px 14px;
        border-radius: 6px;
        color: #475569 !important;
        text-decoration: none !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 600;
        font-size: 0.92rem;
        transition: all 0.2s ease;
    }
    .nav-item:hover {
        background-color: rgba(0, 0, 0, 0.04);
        color: #0f172a !important;
        text-decoration: none !important;
    }
    
    /* Active Link - Professional Soft Grayish Slate Highlight */
    .nav-item.active {
        background-color: rgba(15, 23, 42, 0.08) !important;
        color: #0f172a !important;
        text-decoration: none !important;
    }
    .nav-item.active * {
        color: #0f172a !important;
    }
    .nav-item.active:hover {
        color: #0f172a !important;
        text-decoration: none !important;
    }
    .nav-item .material-icons {
        font-size: 1.15rem;
        margin-right: 12px;
        color: #64748b;
    }
    
    /* Sidebar logout button */
    section[data-testid="stSidebar"] button {
        text-align: left !important;
        justify-content: flex-start !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        font-size: 0.9rem !important;
    }
    
    /* Input custom overrides */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.01) !important;
    }
    input, select {
        color: #0f172a !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Styled general buttons */
    .stButton>button {
        background-color: #ffffff !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        color: #334155 !important;
        border-radius: 6px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.01) !important;
    }
    .stButton>button:hover {
        background-color: #f8fafc !important;
        border-color: rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Primary buttons */
    .stButton>button[kind="primary"] {
        background: #0f172a !important;
        color: white !important;
        border: 1px solid #0f172a !important;
    }
    .stButton>button[kind="primary"]:hover {
        background: #1e293b !important;
        border-color: #1e293b !important;
        transform: translateY(-1px) !important;
    }
    
    /* Double-Bezel nested container */
    .bezel-shell {
        background: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(0, 0, 0, 0.04);
        border-radius: 12px;
        padding: 2px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.01);
        margin-bottom: 15px;
    }
    .bezel-core {
        background: #ffffff;
        border-radius: 10px;
        padding: 22px;
        text-align: left;
        border: 1px solid rgba(0, 0, 0, 0.01);
    }
    .kpi-title {
        font-size: 10px;
        font-weight: 700;
        color: #64748b;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 8px;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        font-family: 'Outfit', sans-serif;
        line-height: 1.0;
        letter-spacing: -0.5px;
    }
    
    /* Brand Header style - Clean Minimalist */
    .brand-header {
        margin-bottom: 35px;
        margin-top: 10px;
        border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        padding-bottom: 20px;
    }
    .brand-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        line-height: 1.1;
        font-family: 'Outfit', sans-serif;
        letter-spacing: -0.5px;
    }
    .brand-desc {
        font-size: 0.95rem;
        color: #475569;
        margin-top: 6px;
        margin-bottom: 0;
        max-width: 65ch;
    }
    
    /* Scraping Console */
    .console-box {
        background-color: #f8fafc;
        color: #475569;
        font-family: 'Courier New', Courier, monospace;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid rgba(0, 0, 0, 0.06);
        max-height: 200px;
        overflow-y: auto;
        font-size: 0.85rem;
        margin-top: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Fetch current stats
stats = get_stats()
db_exists = os.path.exists(DB_PATH)
db_size_kb = os.path.getsize(DB_PATH) / 1024 if db_exists else 0
unique_positions_count = len(stats.get("position_distribution", {}))

# Sidebar inputs for session info, navigation, and logout
with st.sidebar:
    # Logo Inlife
    st.image("https://apply.inlifesurabaya.com/assets/logo_inlife.png", width=120)
    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # Custom HTML Sidebar Navigation Links
    st.markdown("### Navigation")
    
    active_dash = "active" if st.session_state.current_page == "Dashboard" else ""
    active_sync = "active" if st.session_state.current_page == "Sync" else ""
    active_settings = "active" if st.session_state.current_page == "Settings" else ""
    
    st.markdown(f"""
    <div class="sidebar-nav">
        <a href="/?session=authenticated&page=Dashboard" target="_self" class="nav-item {active_dash}">
            <span class="material-icons">dashboard</span>
            <span>Dashboard</span>
        </a>
        <a href="/?session=authenticated&page=Sync" target="_self" class="nav-item {active_sync}">
            <span class="material-icons">sync</span>
            <span>Sync Data</span>
        </a>
        <a href="/?session=authenticated&page=Settings" target="_self" class="nav-item {active_settings}">
            <span class="material-icons">settings</span>
            <span>Configuration</span>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 15px 0; border:0; border-top:1px solid rgba(0,0,0,0.06);'>", unsafe_allow_html=True)
    
    st.markdown("### User Session")
    st.markdown("Role: **Administrator**")
    
    # Logout button
    logout_clicked = st.button("Logout", use_container_width=True, key="sidebar_logout")
    if logout_clicked:
        st.session_state.authenticated = False
        st.query_params.clear()
        st.rerun()
        
    st.markdown("<hr style='margin: 15px 0; border:0; border-top:1px solid rgba(0,0,0,0.06);'>", unsafe_allow_html=True)
    
    st.markdown("### Local Storage")
    st.markdown(f"**Database:** `interns.db`  \n"
                f"**Size:** `{db_size_kb:.1f} KB`  \n"
                f"**Connection:** {'Connected' if db_exists else 'Disconnected'}")

# Render Pages based on Sidebar selection
# ----------------- PAGE 1: DASHBOARD & EXPORT -----------------
if st.session_state.current_page == "Dashboard":
    # Application Header HTML
    st.markdown("""
    <div class="brand-header">
        <h1 class="brand-title">Internship Candidates</h1>
        <p class="brand-desc">Detailed profiles and database query interface for applicants registered through the mentor portal.</p>
    </div>
    """, unsafe_allow_html=True)

    # KPI Cards layout (Dynamic Overview)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="bezel-shell">
            <div class="bezel-core" style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="kpi-title">Total Candidates</div>
                    <div class="kpi-value">{stats.get("total", 0)}</div>
                </div>
                <span class="material-icons" style="color: #64748b; font-size: 1.6rem; margin-top: 2px;">group</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="bezel-shell">
            <div class="bezel-core" style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="kpi-title">Active Positions</div>
                    <div class="kpi-value">{unique_positions_count}</div>
                </div>
                <span class="material-icons" style="color: #64748b; font-size: 1.6rem; margin-top: 2px;">work</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        # Get last scraped timestamp
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT MAX(scraped_at) FROM applicants")
        last_scraped = c.fetchone()[0]
        conn.close()
        
        if last_scraped:
            dt = datetime.fromisoformat(last_scraped)
            formatted_dt = dt.strftime("%d %b %Y, %H:%M")
        else:
            formatted_dt = "No records found"
            
        st.markdown(f"""
        <div class="bezel-shell">
            <div class="bezel-core" style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="kpi-title">Last Updated</div>
                    <div class="kpi-value" style="font-size: 1.45rem; margin-top: 5px; color: #475569;">{formatted_dt}</div>
                </div>
                <span class="material-icons" style="color: #64748b; font-size: 1.6rem; margin-top: 2px;">access_time</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # --- POSITION DISTRIBUTION BREAKDOWN ---
    position_dist = stats.get("position_distribution", {})
    if position_dist:
        with st.container(border=True):
            st.markdown("<h5 style='margin-bottom: 15px; font-family: \"Outfit\"; font-weight: 600;'>Candidate Distribution by Position</h5>", unsafe_allow_html=True)
            total_cand = stats.get("total", 0)
            
            # Split items into two columns
            sorted_dist = sorted(position_dist.items(), key=lambda x: x[1], reverse=True)
            mid = (len(sorted_dist) + 1) // 2
            col_left, col_right = st.columns(2)
            
            with col_left:
                for pos, count in sorted_dist[:mid]:
                    pct = (count / total_cand) * 100 if total_cand > 0 else 0
                    st.markdown(f"""
                    <div style="margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 600; color: #475569; margin-bottom: 4px;">
                            <span>{pos}</span>
                            <span style="color: #0f172a;">{count} ({pct:.1f}%)</span>
                        </div>
                        <div style="background-color: #f1f5f9; border-radius: 100px; height: 6px; width: 100%;">
                            <div style="background-color: #64748b; height: 6px; border-radius: 100px; width: {pct}%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_right:
                for pos, count in sorted_dist[mid:]:
                    pct = (count / total_cand) * 100 if total_cand > 0 else 0
                    st.markdown(f"""
                    <div style="margin-bottom: 14px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 600; color: #475569; margin-bottom: 4px;">
                            <span>{pos}</span>
                            <span style="color: #0f172a;">{count} ({pct:.1f}%)</span>
                        </div>
                        <div style="background-color: #f1f5f9; border-radius: 100px; height: 6px; width: 100%;">
                            <div style="background-color: #64748b; height: 6px; border-radius: 100px; width: {pct}%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # Wrap filters in a beautiful structural container
    with st.container(border=True):
        st.markdown("##### Search Filters")
        
        # Layout filters
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            search_query = st.text_input("Search Name / University / Email", placeholder="Type keywords...")

        with f_col2:
            major_options = ["All Majors"] + get_majors()
            major_filter = st.selectbox("Academic Major", options=major_options, index=0)

        with f_col3:
            default_position_idx = 0
            position_options = ["All Positions"] + get_positions()
            
            # Try to find "SISTEM INFORMASI" index (case-insensitive)
            for idx, opt in enumerate(position_options):
                if opt.upper() == "SISTEM INFORMASI":
                    default_position_idx = idx
                    break
                    
            position_filter = st.selectbox("Applied Position", options=position_options, index=default_position_idx)

    # Translate UI 'Semua' option to database filter (None)
    db_position_filter = None if position_filter == "All Positions" else position_filter
    db_major_filter = None if major_filter == "All Majors" else major_filter

    # Query applicants
    filtered_applicants = get_applicants(
        search_query=search_query, 
        position_filter=db_position_filter, 
        major_filter=db_major_filter
    )

    # Convert to DataFrame
    df = pd.DataFrame(filtered_applicants)

    if not df.empty:
        # Select columns to display in summary table
        display_cols = {
            "name": "Full Name",
            "major": "Academic Major",
            "university": "University",
            "phone_number": "Phone Number",
            "email": "Email Address",
            "position_title": "Position",
            "tahap": "Status"
        }
        
        existing_display_cols = {k: v for k, v in display_cols.items() if k in df.columns}
        df_display = df[list(existing_display_cols.keys())].rename(columns=existing_display_cols)
        
        if "Status" in df_display.columns:
            df_display["Status"] = df_display["Status"].apply(lambda x: str(x).upper() if x else "-")
            
        st.markdown(f"Found **{len(df_display)}** candidates matching criteria.")
        st.dataframe(df_display, use_container_width=True)
        
        # --- EXCEL EXPORT ---
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
        
        st.markdown("### Export Interface")
        st.write("Download formatted Excel document containing: **Nama**, **Nomor WA/HP**, and **Email**.")
        
        # Download button
        st.download_button(
            label=f"Download Excel ({len(export_df)} rows)",
            data=buffer,
            file_name=f"candidates_{position_filter.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=False
        )
    else:
        st.warning("No candidate records matched the current search filters.")
        st.info("Ensure the local cache has been synchronized. Run a sync in the Sync Data menu.")

# ----------------- PAGE 2: SYNCHRONIZE (SCRAPE) -----------------
elif st.session_state.current_page == "Sync":
    st.markdown("""
    <div class="brand-header">
        <h1 class="brand-title">Portal Synchronization</h1>
        <p class="brand-desc">Crawl and sync detailed candidate records from the mentor platform API.</p>
    </div>
    """, unsafe_allow_html=True)
    
    mentor_email = get_setting("mentor_email", "newgen@gmail.com")
    mentor_password = get_setting("mentor_password", "Tapfya88")
    
    st.write(f"Authorized Scraper Account: `{mentor_email}`")
    
    # Sync button
    start_scraping = st.button("Sync Now", use_container_width=True, type="primary")
    
    if start_scraping:
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        console_logs = st.empty()
        
        log_messages = []
        
        def update_logs(msg):
            log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            console_html = "<div class='console-box'>" + "<br>".join(log_messages[::-1]) + "</div>"
            console_logs.markdown(console_html, unsafe_allow_html=True)
            
        try:
            update_logs("Initializing synchronization...")
            for event in scrape_generator(mentor_email, mentor_password):
                if event["type"] == "status":
                    update_logs(event["message"])
                    status_text.info(event["message"])
                    
                elif event["type"] == "progress":
                    current = event["current"]
                    total = event["total"]
                    pct = current / total
                    progress_bar.progress(pct)
                    status_text.info(f"Downloading profile: {current}/{total}")
                    update_logs(event["message"])
                    
                elif event["type"] == "complete":
                    progress_bar.progress(1.0)
                    status_text.success(event["message"])
                    update_logs(event["message"])
                    st.success("Database records updated successfully. Open the Dashboard tab to search.")
                    
                elif event["type"] == "error":
                    status_text.error(event["message"])
                    update_logs(f"ERROR: {event['message']}")
                    
        except Exception as e:
            status_text.error(f"Synchronization halted: {str(e)}")
            update_logs(f"FATAL ERROR: {str(e)}")

# ----------------- PAGE 3: SETTINGS -----------------
elif st.session_state.current_page == "Settings":
    st.markdown("""
    <div class="brand-header">
        <h1 class="brand-title">System Configurations</h1>
        <p class="brand-desc">Configure authentication credentials and manage local database operations.</p>
    </div>
    """, unsafe_allow_html=True)
    
    curr_email = get_setting("mentor_email", "newgen@gmail.com")
    curr_password = get_setting("mentor_password", "Tapfya88")
    
    with st.container(border=True):
        st.markdown("##### Mentor Portal Credentials")
        new_email = st.text_input("Account Email Address", value=curr_email, placeholder="e.g. newgen@gmail.com")
        new_password = st.text_input("Account Password", value=curr_password, type="password", placeholder="Type password...")
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        # Save settings
        save_settings_btn = st.button("Save Settings", type="primary")
        
        if save_settings_btn:
            if not new_email or not new_password:
                st.error("Fields cannot be empty.")
            else:
                set_setting("mentor_email", new_email)
                set_setting("mentor_password", new_password)
                st.success("Credentials saved to local configuration database.")
                st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("##### Cache Maintenance")
        st.write("Wipe cached records from the database table. This action does not affect credentials.")
        
        confirm_clear = st.checkbox("Confirm deletion of all cached candidate profiles.")
        clear_db_btn = st.button("Clear SQLite Cache", disabled=not confirm_clear)
        
        if clear_db_btn and confirm_clear:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM applicants")
                conn.commit()
                conn.close()
                st.success("Database records cleared successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to clear cache: {e}")
