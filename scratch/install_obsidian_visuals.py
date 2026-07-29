import urllib.request
import json
import os

VAULT_DIR = "/home/sjack7/Desktop/Onbrandcraftz/.obsidian"
THEMES_DIR = os.path.join(VAULT_DIR, "themes")
PLUGINS_DIR = os.path.join(VAULT_DIR, "plugins")
SNIPPETS_DIR = os.path.join(VAULT_DIR, "snippets")
APPEARANCE_FILE = os.path.join(VAULT_DIR, "appearance.json")
COMMUNITY_PLUGINS_FILE = os.path.join(VAULT_DIR, "community-plugins.json")

os.makedirs(THEMES_DIR, exist_ok=True)
os.makedirs(PLUGINS_DIR, exist_ok=True)
os.makedirs(SNIPPETS_DIR, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}

# 1. Download Minimal Theme
print("--> Installing Minimal Theme...")
min_dir = os.path.join(THEMES_DIR, "Minimal")
os.makedirs(min_dir, exist_ok=True)
try:
    req = urllib.request.Request("https://api.github.com/repos/kepano/obsidian-minimal/releases/latest", headers=headers)
    with urllib.request.urlopen(req) as resp:
        rel_data = json.loads(resp.read().decode('utf-8'))
    for asset in rel_data.get("assets", []):
        aname = asset["name"]
        if aname in ["theme.css", "manifest.json"]:
            print(f"    Downloading Minimal {aname}...")
            dl_req = urllib.request.Request(asset["browser_download_url"], headers=headers)
            with urllib.request.urlopen(dl_req) as dl_resp:
                with open(os.path.join(min_dir, aname), "wb") as f:
                    f.write(dl_resp.read())
    print("✓ Minimal theme installed.")
except Exception as e:
    print(f"❌ Failed Minimal theme: {e}")

# 2. Download Catppuccin Theme
print("--> Installing Catppuccin Theme...")
cat_dir = os.path.join(THEMES_DIR, "Catppuccin")
os.makedirs(cat_dir, exist_ok=True)
try:
    req = urllib.request.Request("https://api.github.com/repos/catppuccin/obsidian/releases/latest", headers=headers)
    with urllib.request.urlopen(req) as resp:
        rel_data = json.loads(resp.read().decode('utf-8'))
    for asset in rel_data.get("assets", []):
        aname = asset["name"]
        if aname in ["theme.css", "manifest.json"]:
            print(f"    Downloading Catppuccin {aname}...")
            dl_req = urllib.request.Request(asset["browser_download_url"], headers=headers)
            with urllib.request.urlopen(dl_req) as dl_resp:
                with open(os.path.join(cat_dir, aname), "wb") as f:
                    f.write(dl_resp.read())
    print("✓ Catppuccin theme installed.")
except Exception as e:
    print(f"❌ Failed Catppuccin theme: {e}")

# 3. Download Style Settings Plugin
print("--> Installing Style Settings Plugin...")
ss_dir = os.path.join(PLUGINS_DIR, "obsidian-style-settings")
os.makedirs(ss_dir, exist_ok=True)
try:
    req = urllib.request.Request("https://api.github.com/repos/mgmeyers/obsidian-style-settings/releases/latest", headers=headers)
    with urllib.request.urlopen(req) as resp:
        rel_data = json.loads(resp.read().decode('utf-8'))
    for asset in rel_data.get("assets", []):
        aname = asset["name"]
        if aname in ["main.js", "manifest.json", "styles.css"]:
            print(f"    Downloading Style Settings {aname}...")
            dl_req = urllib.request.Request(asset["browser_download_url"], headers=headers)
            with urllib.request.urlopen(dl_req) as dl_resp:
                with open(os.path.join(ss_dir, aname), "wb") as f:
                    f.write(dl_resp.read())
    print("✓ Style Settings plugin installed.")
    
    # Enable in community-plugins.json
    if os.path.exists(COMMUNITY_PLUGINS_FILE):
        with open(COMMUNITY_PLUGINS_FILE, 'r') as f:
            cplugins = json.load(f)
    else:
        cplugins = []
    if "obsidian-style-settings" not in cplugins:
        cplugins.append("obsidian-style-settings")
    with open(COMMUNITY_PLUGINS_FILE, 'w') as f:
        json.dump(cplugins, f, indent=2)
except Exception as e:
    print(f"❌ Failed Style Settings plugin: {e}")

# 4. Set Minimal theme as default cssTheme in appearance.json
app_conf = {
    "theme": "obsidian",
    "baseColorScheme": "dark",
    "cssTheme": "Minimal",
    "enabledCssSnippets": ["custom-dashboard-accents"]
}
with open(APPEARANCE_FILE, 'w') as f:
    json.dump(app_conf, f, indent=2)

print("✓ Set cssTheme to Minimal in appearance.json")

# 5. Create a sleek CSS snippet for custom card borders, glow accents & callouts
snippet_css = """
/* Executive Dashboard & Visual Accents */
.markdown-rendered h1 {
  color: #c9a84c;
  border-bottom: 1px solid rgba(201, 168, 76, 0.2);
  padding-bottom: 8px;
  letter-spacing: -0.5px;
}

.markdown-rendered blockquote {
  border-left: 3px solid #c9a84c;
  background: rgba(201, 168, 76, 0.05);
  border-radius: 0 8px 8px 0;
  padding: 12px 16px;
}

/* Dataview Table Visual Polish */
.dataview.table-view-table {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.dataview.table-view-table th {
  background: rgba(201, 168, 76, 0.12);
  color: #c9a84c;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.5px;
}

/* Kanban Cards Glow */
.kanban-plugin__item {
  border-radius: 8px !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
  transition: transform 0.2s, border-color 0.2s !important;
}
.kanban-plugin__item:hover {
  border-color: rgba(201, 168, 76, 0.4) !important;
  transform: translateY(-2px) !important;
}
"""
with open(os.path.join(SNIPPETS_DIR, "custom-dashboard-accents.css"), "w") as f:
    f.write(snippet_css)

print("✓ Created custom-dashboard-accents.css snippet.")
