import urllib.request
import json
import os

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://github.com/SoftFever/OrcaSlicer/releases/download/v2.4.2/OrcaSlicer_Linux_AppImage_Ubuntu2404_V2.4.2.AppImage"
dest = "/home/sjack7/Downloads/OrcaSlicer_Linux_AppImage_Ubuntu2404_V2.4.2.AppImage"

print(f"Downloading OrcaSlicer AppImage: {url}...")
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
print("✓ OrcaSlicer AppImage downloaded and Desktop launcher configured!")
