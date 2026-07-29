import urllib.request
import json
import os
import tarfile
import subprocess

LOCAL_BIN = "/home/sjack7/.local/bin"
DOWNLOADS_DIR = "/home/sjack7/Downloads"
DESKTOP_DIR = "/home/sjack7/Desktop"

os.makedirs(LOCAL_BIN, exist_ok=True)
headers = {"User-Agent": "Mozilla/5.0"}

# 1. Download OrcaSlicer AppImage
print("--> Downloading OrcaSlicer...")
try:
    req = urllib.request.Request("https://api.github.com/repos/SoftFever/OrcaSlicer/releases/latest", headers=headers)
    with urllib.request.urlopen(req) as resp:
        rel_data = json.loads(resp.read().decode('utf-8'))
    
    appimage_url = None
    for asset in rel_data.get("assets", []):
        aname = asset["name"]
        if "Linux" in aname and aname.endswith(".AppImage"):
            appimage_url = asset["browser_download_url"]
            appimage_name = aname
            break
            
    if appimage_url:
        dest_path = os.path.join(DOWNLOADS_DIR, appimage_name)
        print(f"    Downloading {appimage_name}...")
        dl_req = urllib.request.Request(appimage_url, headers=headers)
        with urllib.request.urlopen(dl_req) as dl_resp:
            with open(dest_path, "wb") as f:
                f.write(dl_resp.read())
        os.chmod(dest_path, 0o755)
        
        # Create Desktop shortcut for OrcaSlicer
        desktop_file = os.path.join(DESKTOP_DIR, "OrcaSlicer.desktop")
        with open(desktop_file, "w") as f:
            f.write(f"""[Desktop Entry]
Name=OrcaSlicer
Exec={dest_path} %F
Icon=orca-slicer
Type=Application
Categories=Graphics;3DGraphics;Engineering;
Terminal=false
StartupNotify=true
""")
        os.chmod(desktop_file, 0o755)
        print("✓ OrcaSlicer downloaded and Desktop launcher created!")
except Exception as e:
    print(f"❌ Failed to download OrcaSlicer: {e}")

# 2. Install Ollama standalone binary
print("--> Downloading Ollama local AI engine...")
try:
    tar_url = "https://ollama.com/download/ollama-linux-amd64.tgz"
    tar_path = os.path.join(DOWNLOADS_DIR, "ollama.tgz")
    print("    Downloading ollama-linux-amd64.tgz...")
    dl_req = urllib.request.Request(tar_url, headers=headers)
    with urllib.request.urlopen(dl_req) as dl_resp:
        with open(tar_path, "wb") as f:
            f.write(dl_resp.read())
    
    # Extract binary to LOCAL_BIN
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith("ollama"):
                f_obj = tar.extractfile(member)
                if f_obj:
                    dest_bin = os.path.join(LOCAL_BIN, "ollama")
                    with open(dest_bin, "wb") as out:
                        out.write(f_obj.read())
                    os.chmod(dest_bin, 0o755)
                    print("✓ Ollama binary installed in ~/.local/bin/ollama")
                    break
except Exception as e:
    print(f"❌ Failed to install Ollama: {e}")
