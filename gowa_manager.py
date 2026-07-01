import os
import sys
import platform
import urllib.request
import json
import zipfile
import tarfile
import subprocess
import time
import atexit
import shutil

gowa_process = None

def download_gowa():
    """Queries GitHub API to download GOWA matching release package for the OS."""
    bin_dir = os.path.join(os.path.dirname(__file__), "bin")
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)
        
    system = platform.system().lower()  # 'windows', 'darwin', 'linux'
    machine = platform.machine().lower()  # 'amd64', 'x86_64', 'arm64'
    
    print(f"[GOWA] System detected: OS={system}, Arch={machine}")
    
    try:
        api_url = "https://api.github.com/repos/aldinokemal/go-whatsapp-web-multidevice/releases/latest"
        req = urllib.request.Request(
            api_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            release_data = json.loads(response.read().decode())
            
        assets = release_data.get("assets", [])
        
        # Map OS names
        os_keyword = ""
        arch_keyword = ""
        
        if system == "darwin":
            os_keyword = "darwin"
            if "arm" in machine or "aarch" in machine:
                arch_keyword = "arm64"
            else:
                arch_keyword = "amd64"
        elif system == "windows":
            os_keyword = "windows"
            arch_keyword = "amd64"
        else:
            os_keyword = "linux"
            if "arm" in machine or "aarch" in machine:
                arch_keyword = "arm64"
            else:
                arch_keyword = "amd64"
                
        download_url = None
        asset_name = None
        
        # Look for matching asset package
        for asset in assets:
            name = asset.get("name", "").lower()
            if os_keyword in name and arch_keyword in name:
                download_url = asset.get("browser_download_url")
                asset_name = asset.get("name")
                break
                
        if not download_url:
            # Fallback
            for asset in assets:
                name = asset.get("name", "").lower()
                if os_keyword in name:
                    download_url = asset.get("browser_download_url")
                    asset_name = asset.get("name")
                    break
                    
        if not download_url:
            print("[GOWA] Could not find matching precompiled binary asset on GitHub releases.")
            return False
            
        archive_path = os.path.join(bin_dir, asset_name)
        print(f"[GOWA] Downloading release package: {asset_name}...")
        
        # Download package
        with urllib.request.urlopen(download_url) as dl_stream:
            with open(archive_path, "wb") as out_file:
                shutil.copyfileobj(dl_stream, out_file)
                
        print("[GOWA] Extracting archive package...")
        # Extract archive
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(bin_dir)
        elif archive_path.endswith(".tar.gz") or archive_path.endswith(".tgz"):
            with tarfile.open(archive_path, "r:gz") as tar_ref:
                tar_ref.extractall(bin_dir)
                
        # Clean archive file
        try:
            os.remove(archive_path)
        except Exception:
            pass
            
        print("[GOWA] Release files extracted successfully.")
        return True
    except Exception as e:
        print("[GOWA] Download failed. Error: ", str(e))
        return False

def get_gowa_binary_path():
    """Searches bin/ folder for GOWA executable."""
    bin_dir = os.path.join(os.path.dirname(__file__), "bin")
    system = platform.system().lower()
    ext = ".exe" if system == "windows" else ""
    
    # First search for standard binary 'whatsapp' / 'whatsapp.exe'
    p1 = os.path.join(bin_dir, f"whatsapp{ext}")
    if os.path.exists(p1):
        try:
            os.chmod(p1, 0o755)
        except Exception:
            pass
        return p1
        
    # Walk folder for executables
    for root, dirs, files in os.walk(bin_dir):
        for f in files:
            if f.startswith("whatsapp") or "go-whatsapp" in f:
                if system == "windows" and f.endswith(".exe"):
                    return os.path.join(root, f)
                elif system != "windows" and not f.endswith((".zip", ".tar.gz", ".txt", ".md", ".json")):
                    path = os.path.join(root, f)
                    try:
                        os.chmod(path, 0o755)
                    except Exception:
                        pass
                    return path
    return None

def start_gowa():
    """Launches GOWA daemon in background on port 3000."""
    global gowa_process
    
    # 1. Ping check if port 3000 is already active
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:3000", timeout=1) as conn:
            if conn.status < 500:
                print("[GOWA] Service is already active on port 3000.")
                return True
    except Exception:
        pass
        
    # 2. Check binary
    bin_path = get_gowa_binary_path()
    if not bin_path:
        print("[GOWA] Binary not found. Starting automatic downloader...")
        download_success = download_gowa()
        if not download_success:
            return False
        bin_path = get_gowa_binary_path()
        if not bin_path:
            return False
            
    # 3. Spawn process
    try:
        creationflags = 0
        if platform.system().lower() == "windows":
            creationflags = 0x08000000  # CREATE_NO_WINDOW
            
        print(f"[GOWA] Spawning daemon: {bin_path} rest")
        gowa_process = subprocess.Popen(
            [bin_path, "rest"],
            cwd=os.path.dirname(bin_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )
        # Give GOWA a couple seconds to boot
        time.sleep(2)
        print("[GOWA] Background daemon is running.")
        return True
    except Exception as err:
        print("[GOWA] Failed to spawn background daemon:", str(err))
        return False

def cleanup_gowa():
    """Callback to terminate GOWA process cleanly."""
    global gowa_process
    if gowa_process:
        try:
            print("[GOWA] Shutting down background daemon...")
            gowa_process.terminate()
            gowa_process.wait(timeout=2)
            print("[GOWA] Shutdown complete.")
        except Exception:
            pass

# Register callback
atexit.register(cleanup_gowa)
