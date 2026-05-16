"""
Windows Laptop Optimization Tool
Cleans temp files, optimizes memory, manages startup items, and more.
Run as Administrator for full functionality.
"""

import os
import sys
import shutil
import subprocess
import ctypes
import platform
import tempfile
import winreg
import psutil
from pathlib import Path
from datetime import datetime


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def require_windows():
    if platform.system() != "Windows":
        print("[ERROR] This tool only runs on Windows.")
        sys.exit(1)


def header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def status(msg, ok=True):
    icon = "[OK]" if ok else "[WARN]"
    print(f"  {icon} {msg}")


# ---------------------------------------------------------------------------
# 1. Temp file cleanup
# ---------------------------------------------------------------------------

TEMP_DIRS = [
    Path(os.environ.get("TEMP", "")),
    Path(os.environ.get("TMP", "")),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Temp",
    Path("C:/Windows/Temp"),
    Path("C:/Windows/Prefetch"),
]

def _remove_path(p: Path) -> int:
    """Remove a file or directory tree; return bytes freed."""
    try:
        size = p.stat().st_size if p.is_file() else sum(
            f.stat().st_size for f in p.rglob("*") if f.is_file()
        )
        if p.is_file():
            p.unlink()
        else:
            shutil.rmtree(p, ignore_errors=True)
        return size
    except (PermissionError, FileNotFoundError, OSError):
        return 0


def clean_temp_files():
    header("Temp File Cleanup")
    total_freed = 0
    for d in TEMP_DIRS:
        if not d.exists():
            continue
        for item in d.iterdir():
            total_freed += _remove_path(item)
    freed_mb = total_freed / (1024 * 1024)
    status(f"Freed {freed_mb:.1f} MB from temp directories")
    return freed_mb


# ---------------------------------------------------------------------------
# 2. Recycle Bin empty
# ---------------------------------------------------------------------------

def empty_recycle_bin():
    header("Recycle Bin")
    try:
        # SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND = 7
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        status("Recycle Bin emptied")
    except Exception as e:
        status(f"Could not empty Recycle Bin: {e}", ok=False)


# ---------------------------------------------------------------------------
# 3. Windows Update cache cleanup
# ---------------------------------------------------------------------------

def clean_windows_update_cache():
    header("Windows Update Cache")
    cache_dir = Path("C:/Windows/SoftwareDistribution/Download")
    if not cache_dir.exists():
        status("Cache directory not found — skipping", ok=False)
        return 0
    freed = 0
    for item in cache_dir.iterdir():
        freed += _remove_path(item)
    freed_mb = freed / (1024 * 1024)
    status(f"Freed {freed_mb:.1f} MB from Windows Update cache")
    return freed_mb


# ---------------------------------------------------------------------------
# 4. DNS cache flush
# ---------------------------------------------------------------------------

def flush_dns():
    header("DNS Cache")
    try:
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, check=True)
        status("DNS cache flushed")
    except subprocess.CalledProcessError as e:
        status(f"DNS flush failed: {e}", ok=False)


# ---------------------------------------------------------------------------
# 5. Memory report
# ---------------------------------------------------------------------------

def report_memory():
    header("Memory Status")
    vm = psutil.virtual_memory()
    used_gb = vm.used / (1024 ** 3)
    total_gb = vm.total / (1024 ** 3)
    avail_gb = vm.available / (1024 ** 3)
    print(f"  Total  : {total_gb:.1f} GB")
    print(f"  Used   : {used_gb:.1f} GB  ({vm.percent}%)")
    print(f"  Free   : {avail_gb:.1f} GB")
    if vm.percent > 85:
        status("High memory usage detected — consider closing unused apps", ok=False)
    else:
        status("Memory usage looks healthy")


# ---------------------------------------------------------------------------
# 6. Top CPU / memory hogs
# ---------------------------------------------------------------------------

def report_top_processes(n=10):
    header(f"Top {n} Processes by CPU + Memory")
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            info = p.info
            mem_mb = (info["memory_info"].rss if info["memory_info"] else 0) / (1024 ** 2)
            procs.append((info["name"], info["cpu_percent"], mem_mb, info["pid"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    procs.sort(key=lambda x: (x[1], x[2]), reverse=True)
    print(f"  {'PID':>6}  {'CPU%':>6}  {'MEM(MB)':>9}  NAME")
    print(f"  {'-'*6}  {'-'*6}  {'-'*9}  {'-'*30}")
    for name, cpu, mem, pid in procs[:n]:
        print(f"  {pid:>6}  {cpu:>6.1f}  {mem:>9.1f}  {name}")


# ---------------------------------------------------------------------------
# 7. Disk usage summary
# ---------------------------------------------------------------------------

def report_disk_usage():
    header("Disk Usage")
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            pct = usage.percent
            bar_len = 30
            filled = int(bar_len * pct / 100)
            bar = "#" * filled + "-" * (bar_len - filled)
            print(f"\n  Drive  : {part.device}  ({part.fstype})")
            print(f"  [{bar}] {pct}%")
            print(f"  Total {total_gb:.1f} GB | Used {used_gb:.1f} GB | Free {free_gb:.1f} GB")
            if pct > 90:
                status(f"Drive {part.device} is almost full!", ok=False)
        except PermissionError:
            pass


# ---------------------------------------------------------------------------
# 8. Startup programs (registry)
# ---------------------------------------------------------------------------

STARTUP_KEYS = [
    (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
]

def list_startup_programs():
    header("Startup Programs")
    entries = []
    for hive, subkey in STARTUP_KEYS:
        try:
            key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    hive_name = "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM"
                    entries.append((hive_name, name, value))
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except (FileNotFoundError, PermissionError):
            pass

    if not entries:
        status("No startup programs found in registry")
        return entries

    print(f"  {'HIVE':5}  {'NAME':<35}  COMMAND")
    print(f"  {'-'*5}  {'-'*35}  {'-'*40}")
    for hive_name, name, value in entries:
        short_val = value[:60] + "..." if len(value) > 60 else value
        print(f"  {hive_name:5}  {name:<35}  {short_val}")
    print(f"\n  Total startup entries: {len(entries)}")
    if len(entries) > 15:
        status("Many startup programs detected — review and disable unneeded ones", ok=False)
    return entries


# ---------------------------------------------------------------------------
# 9. Power plan — set to Balanced or High Performance
# ---------------------------------------------------------------------------

POWER_PLANS = {
    "balanced":         "381b4222-f694-41f0-9685-ff5bb260df2e",
    "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635b",
    "power_saver":      "a1841308-3541-4fab-bc81-f71556f20b4a",
}

def set_power_plan(plan: str = "balanced"):
    header("Power Plan")
    guid = POWER_PLANS.get(plan.lower().replace(" ", "_"))
    if not guid:
        status(f"Unknown plan '{plan}'. Choose: balanced, high_performance, power_saver", ok=False)
        return
    try:
        subprocess.run(["powercfg", "/setactive", guid], capture_output=True, check=True)
        status(f"Power plan set to: {plan}")
    except subprocess.CalledProcessError as e:
        status(f"Could not set power plan: {e}", ok=False)


# ---------------------------------------------------------------------------
# 10. Disable visual effects for performance
# ---------------------------------------------------------------------------

def optimize_visual_effects():
    header("Visual Effects")
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                             winreg.KEY_SET_VALUE | winreg.KEY_READ)
        # VisualFXSetting: 2 = Adjust for best performance, 1 = best appearance, 3 = custom
        winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 2)
        winreg.CloseKey(key)
        status("Visual effects set to 'Best Performance' (takes effect on next login)")
    except (FileNotFoundError, PermissionError) as e:
        status(f"Could not update visual effects: {e}", ok=False)


# ---------------------------------------------------------------------------
# 11. Run Windows built-in Disk Cleanup (silent)
# ---------------------------------------------------------------------------

def run_disk_cleanup():
    header("Windows Disk Cleanup (cleanmgr)")
    try:
        # /sagerun:1 runs with preset flags; /sageset:1 lets you pick first
        subprocess.Popen(["cleanmgr", "/sagerun:1"])
        status("Disk Cleanup launched (runs in background)")
    except FileNotFoundError:
        status("cleanmgr not found — skipping", ok=False)


# ---------------------------------------------------------------------------
# 12. SFC / DISM health check (optional, slow)
# ---------------------------------------------------------------------------

def run_sfc_scan():
    header("System File Checker (sfc /scannow)")
    if not is_admin():
        status("Admin rights required — skipping SFC scan", ok=False)
        return
    print("  Running sfc /scannow — this may take several minutes ...")
    try:
        result = subprocess.run(["sfc", "/scannow"], capture_output=True, text=True, timeout=600)
        lines = result.stdout.strip().splitlines()
        for line in lines[-5:]:
            print(f"  {line}")
        status("SFC scan complete")
    except subprocess.TimeoutExpired:
        status("SFC scan timed out", ok=False)
    except Exception as e:
        status(f"SFC scan error: {e}", ok=False)


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

TASKS = {
    "1": ("Clean temp files",                  clean_temp_files),
    "2": ("Empty Recycle Bin",                 empty_recycle_bin),
    "3": ("Clean Windows Update cache",        clean_windows_update_cache),
    "4": ("Flush DNS cache",                   flush_dns),
    "5": ("Memory report",                     report_memory),
    "6": ("Top processes (CPU + RAM)",         report_top_processes),
    "7": ("Disk usage report",                 report_disk_usage),
    "8": ("List startup programs",             list_startup_programs),
    "9": ("Set power plan (balanced)",         lambda: set_power_plan("balanced")),
    "10": ("Set power plan (high performance)",lambda: set_power_plan("high_performance")),
    "11": ("Optimize visual effects",          optimize_visual_effects),
    "12": ("Launch Disk Cleanup (cleanmgr)",   run_disk_cleanup),
    "13": ("Run SFC system file check (slow)", run_sfc_scan),
    "A": ("Run ALL quick optimizations",       None),
    "Q": ("Quit",                              None),
}

QUICK_TASKS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "11"]


def print_menu():
    print("\n" + "="*60)
    print("  Windows Laptop Optimizer")
    if is_admin():
        print("  [Running as Administrator]")
    else:
        print("  [Running as Standard User — some features limited]")
    print("="*60)
    for key, (desc, _) in TASKS.items():
        print(f"  [{key:>2}]  {desc}")
    print()


def run_quick_all():
    header("Running All Quick Optimizations")
    total_freed = 0.0
    for key in QUICK_TASKS:
        _, fn = TASKS[key]
        result = fn()
        if isinstance(result, (int, float)):
            total_freed += result
    header("Optimization Complete")
    if total_freed > 0:
        print(f"  Total disk space freed: {total_freed:.1f} MB")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Finished at: {timestamp}")


def main():
    require_windows()

    if len(sys.argv) > 1 and sys.argv[1].lower() in ("--auto", "-a"):
        run_quick_all()
        return

    while True:
        print_menu()
        choice = input("  Enter choice: ").strip().upper()

        if choice == "Q":
            print("  Goodbye!")
            break
        elif choice == "A":
            run_quick_all()
        elif choice in TASKS:
            _, fn = TASKS[choice]
            fn()
        else:
            print("  Invalid choice — try again.")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()
