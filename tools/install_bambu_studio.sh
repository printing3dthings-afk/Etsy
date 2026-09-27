#!/bin/sh
# Install Bambu Studio for tools/bambu_slicer.py (see its docstring for why
# Flathub and bubblewrap rather than the GitHub AppImage). ~1.4 GB, a few
# minutes. Safe to re-run.
set -e
if ! command -v flatpak >/dev/null || ! command -v bwrap >/dev/null; then
    apt-get install -y flatpak bubblewrap || { apt-get update && apt-get install -y flatpak bubblewrap; }
fi
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install -y --noninteractive flathub com.bambulab.BambuStudio
python3 "$(dirname "$0")/bambu_slicer.py" --check
