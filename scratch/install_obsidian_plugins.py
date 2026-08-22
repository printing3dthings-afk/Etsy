import urllib.request
import json
import os

VAULT_PLUGINS_DIR = "/home/sjack7/Desktop/Onbrandcraftz/.obsidian/plugins"
COMMUNITY_PLUGINS_FILE = "/home/sjack7/Desktop/Onbrandcraftz/.obsidian/community-plugins.json"

# Beneficial plugins for business, task management, automation, & knowledge base
PLUGINS = [
    {"id": "dataview", "repo": "blacksmithgu/obsidian-dataview", "name": "Dataview"},
    {"id": "obsidian-kanban", "repo": "mgmeyers/obsidian-kanban", "name": "Kanban"},
    {"id": "templater-obsidian", "repo": "SilentVoid13/Templater", "name": "Templater"},
    {"id": "obsidian-tasks-plugin", "repo": "obsidian-tasks-group/obsidian-tasks", "name": "Tasks"},
    {"id": "table-editor-obsidian", "repo": "tgrosinger/advanced-tables-obsidian", "name": "Advanced Tables"},
    {"id": "tag-wrangler", "repo": "pjeby/tag-wrangler", "name": "Tag Wrangler"}
]

os.makedirs(VAULT_PLUGINS_DIR, exist_ok=True)

# Load existing community plugins
if os.path.exists(COMMUNITY_PLUGINS_FILE):
    with open(COMMUNITY_PLUGINS_FILE, 'r') as f:
        try:
            enabled_plugins = json.load(f)
        except Exception:
            enabled_plugins = []
else:
    enabled_plugins = []

headers = {"User-Agent": "Mozilla/5.0"}

for p in PLUGINS:
    pid = p["id"]
    repo = p["repo"]
    name = p["name"]
    print(f"--> Installing {name} ({pid})...")
    
    target_dir = os.path.join(VAULT_PLUGINS_DIR, pid)
    os.makedirs(target_dir, exist_ok=True)
    
    # Get latest release from GitHub API
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            rel_data = json.loads(resp.read().decode('utf-8'))
        
        assets = rel_data.get("assets", [])
        for asset in assets:
            aname = asset["name"]
            if aname in ["main.js", "manifest.json", "styles.css"]:
                download_url = asset["browser_download_url"]
                dest_path = os.path.join(target_dir, aname)
                print(f"    Downloading {aname}...")
                dl_req = urllib.request.Request(download_url, headers=headers)
                with urllib.request.urlopen(dl_req) as dl_resp:
                    content = dl_resp.read()
                with open(dest_path, "wb") as out_file:
                    out_file.write(content)
        
        if pid not in enabled_plugins:
            enabled_plugins.append(pid)
        print(f"✓ {name} installed successfully.")
    except Exception as e:
        print(f"❌ Failed to install {name}: {e}")

# Save updated community-plugins.json
with open(COMMUNITY_PLUGINS_FILE, "w") as f:
    json.dump(enabled_plugins, f, indent=2)

print("\nUpdated enabled community plugins list:")
print(json.dumps(enabled_plugins, indent=2))
