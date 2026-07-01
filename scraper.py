import requests
from bs4 import BeautifulSoup
import re
import json
import time
from db import save_applicant

BASE_URL = "https://apply.inlifesurabaya.com"

def get_csrf_token():
    """
    Fetches the login page and parses the hardcoded CSRF token from the inline script.
    """
    session = requests.Session()
    login_url = f"{BASE_URL}/login"
    
    response = session.get(login_url)
    if response.status_code != 200:
        raise Exception(f"Gagal memuat halaman login. HTTP Status: {response.status_code}")
        
    soup = BeautifulSoup(response.text, "html.parser")
    
    csrf_token = None
    scripts = soup.find_all("script")
    for s in scripts:
        if s.text and "X-CSRF-TOKEN" in s.text:
            # Match pattern "X-CSRF-TOKEN": "value"
            match = re.search(r'"X-CSRF-TOKEN":\s*"([^"]+)"', s.text)
            if match:
                csrf_token = match.group(1)
                break
                
    return csrf_token, session

def login_mentor(email, password):
    """
    Performs API login and returns JWT access token.
    """
    csrf_token, session = get_csrf_token()
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if csrf_token:
        headers["X-CSRF-TOKEN"] = csrf_token
        
    payload = {
        "email": email,
        "password": password
    }
    
    login_response = session.post(f"{BASE_URL}/api/login", json=payload, headers=headers)
    if login_response.status_code != 200:
        try:
            err_msg = login_response.json().get("message", "Unknown error")
        except:
            err_msg = login_response.text
        raise Exception(f"Gagal login: {err_msg}")
        
    data = login_response.json()
    if data.get("status") != "success":
        raise Exception(f"Gagal login: {data.get('message', 'Login status not success')}")
        
    return data.get("access_token")

def scrape_generator(email, password):
    """
    A generator that logs in, crawls the applicant list, fetches details,
    and updates SQLite. Yields progress updates for the Streamlit UI.
    """
    try:
        yield {"type": "status", "message": "Menghubungkan ke server Inlife..."}
        
        # 1. Login
        token = login_mentor(email, password)
        yield {"type": "status", "message": "Login berhasil! Memulai penarikan data..."}
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        # 2. Fetch page 1 to see total page count
        yield {"type": "status", "message": "Mengambil data daftar pelamar halaman 1..."}
        page1_url = f"{BASE_URL}/api/mentor/jobapplicants?page=1"
        res = requests.get(page1_url, headers=headers)
        
        if res.status_code != 200:
            raise Exception(f"Gagal mengambil daftar pelamar. HTTP Status: {res.status_code}")
            
        res_data = res.json()
        data_field = res_data.get("data", {})
        
        applicants_summary = []
        if isinstance(data_field, dict):
            last_page = data_field.get("last_page", 1)
            total_items = data_field.get("total", 0)
            applicants_summary.extend(data_field.get("data", []))
        else:
            last_page = 1
            total_items = 0
            
        yield {"type": "status", "message": f"Ditemukan total {total_items} pelamar (Halaman 1/{last_page})."}
        
        # Fetch remaining summary pages
        for page in range(2, last_page + 1):
            yield {"type": "status", "message": f"Mengambil data daftar pelamar halaman {page}/{last_page}..."}
            page_url = f"{BASE_URL}/api/mentor/jobapplicants?page={page}"
            p_res = requests.get(page_url, headers=headers)
            if p_res.status_code == 200:
                p_data = p_res.json()
                p_data_field = p_data.get("data", {})
                if isinstance(p_data_field, dict):
                    applicants_summary.extend(p_data_field.get("data", []))
            # Minor sleep to avoid hammering
            time.sleep(0.1)
            
        total_scraped_summary = len(applicants_summary)
        yield {"type": "status", "message": f"Selesai mengumpulkan {total_scraped_summary} ringkasan pelamar. Memulai penarikan detail..."}
        
        # 3. Fetch detailed data for each applicant and save
        success_count = 0
        for i, app_summary in enumerate(applicants_summary):
            app_id = app_summary.get("id")
            app_name = app_summary.get("user", {}).get("name", f"Pelamar #{app_id}")
            
            yield {
                "type": "progress",
                "current": i + 1,
                "total": total_scraped_summary,
                "message": f"[{i + 1}/{total_scraped_summary}] Menarik detail: {app_name}"
            }
            
            try:
                detail_url = f"{BASE_URL}/api/mentor/jobapplicant/{app_id}"
                d_res = requests.get(detail_url, headers=headers)
                if d_res.status_code == 200:
                    d_data = d_res.json()
                    if d_data.get("status") == "success" and "data" in d_data:
                        save_applicant(d_data["data"])
                        success_count += 1
                else:
                    # Log failure silently, continue with other applicants
                    print(f"Failed to fetch detail for {app_id}: HTTP {d_res.status_code}")
            except Exception as e:
                print(f"Error fetching detail for {app_id}: {e}")
                
            # Rate limiting / polite scraping
            time.sleep(0.05)
            
        yield {
            "type": "complete",
            "message": f"Selesai menarik data! Berhasil menyimpan/memperbarui {success_count} data pelamar ke SQLite.",
            "count": success_count
        }
        
    except Exception as e:
        yield {"type": "error", "message": f"Terjadi kesalahan saat scraping: {str(e)}"}
