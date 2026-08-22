import urllib.request
import json
import os

headers = {"User-Agent": "Mozilla/5.0"}
req = urllib.request.Request("https://api.github.com/repos/SoftFever/OrcaSlicer/releases/latest", headers=headers)
with urllib.request.urlopen(req) as resp:
    rel_data = json.loads(resp.read().decode('utf-8'))

for asset in rel_data.get("assets", []):
    aname = asset["name"]
    if "Linux" in aname and "x86_64" in aname or "x64" in aname or "Ubuntu2404_V" in aname:
        print(f"Downloading x86_64 OrcaSlicer: {aname}...")
        url = asset["browser_download_url"]
        dest = f"/home/sjack7/Downloads/{aname}"
        dl_req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(dl_req) as dl_resp:
            with open(dest, "wb") as f:
                f.write(dl_resp.read())
        os.chmod(dest, 0o755)
        
        desktop_file = "/home/sjack7/Desktop/OrcaSlicer.desktop"
        with open(desktop_file, "w") as f:
            f.write(f"""[Desktop Entry]
Name=OrcaSlicer
Exec={dest} %F
Icon=orca-slicer
Type=Application
Categories=Graphics;3DGraphics;Engineering;
Terminal=false
StartupNotify=true
""")
        os.chmod(desktop_file, 0o755)
        print("✓ Updated OrcaSlicer x86_64 AppImage and Desktop launcher!")
        break
