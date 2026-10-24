# Running the printer bridge on an old laptop

The bridge is the small program that connects Frank to the P1S. Frank lives
in the cloud and cannot reach your home network, so something at home has to
run the bridge. With it running, Frank shows the printer live, and a print you
approve in the Action Center starts on the printer.

This guide sets up an old laptop to do that by itself, all the time: it starts
when the laptop turns on, restarts if it stops, and picks up updates on its
own. About 30 minutes, once. It is written for Windows; Mac notes are at the
end.

## 1. Put the laptop near the printer

- **Same network as the printer.** The same Wi-Fi, or better, a network cable
  into your router.
- **Plugged in for good.** Remove the battery if it is swollen or very old.

## 2. Make sure it never sleeps

- **Settings → System → Power & battery → Screen and sleep:** set "When
  plugged in, put my device to sleep after" to **Never**. The screen turning
  off is fine.
- **Control Panel → Power Options → Choose what closing the lid does:** set
  "When I close the lid" (plugged in) to **Do nothing**, then **Save changes**.
  Now you can close it and tuck it away.

## 3. Install Python and Git

- **Python:** python.org → Downloads → Python 3.12 (or newer) for Windows. In
  the installer, **tick "Add python.exe to PATH"** at the bottom of the first
  screen, then Install Now.
- **Git:** git-scm.com → Download for Windows, run it, and accept every
  default.

Check both: open **Command Prompt** (Start → type `cmd`) and run:

```
python --version
git --version
```

Each should print a version number.

## 4. Get the code

In Command Prompt:

```
cd %USERPROFILE%
git clone -b claude/etsy-automation-agents-WFAPU https://github.com/printing3dthings-afk/Etsy.git
cd Etsy
python -m pip install -r tools\relay\bambu_requirements.txt
```

The repository is private, so `git clone` opens a GitHub sign-in window the
first time. Sign in as printing3dthings-afk. It remembers you after that,
which is what lets the bridge update itself later.

## 5. Tell the bridge where everything is

Create the file `tools\relay\.env`:

```
notepad tools\relay\.env
```

Notepad asks to create it: say Yes. Paste this, fill in the four blanks, save:

```
BAMBU_IP=
BAMBU_ACCESS_CODE=
BAMBU_SERIAL=
FRANK_API_BASE=https://etsy-production-b2f1.up.railway.app
APP_SECRET_TOKEN=
```

- **BAMBU_IP, BAMBU_ACCESS_CODE:** on the printer's screen, **Settings →
  Network**. (They are also in Bambu Studio's Device tab.)
- **BAMBU_SERIAL:** printer screen, **Settings → Device**, or the sticker on
  the back.
- **APP_SECRET_TOKEN:** the same value as in Railway (Etsy service →
  Variables).

This file never leaves the laptop: it is excluded from git, so it is never
uploaded.

**Recommended:** in your router's app, reserve the printer's IP address (often
called "DHCP reservation" or "fixed IP"). Otherwise the router can hand the
printer a new address one day and the bridge loses it.

Now test, still in Command Prompt in the `Etsy` folder:

```
python tools\relay\bambu_p1s_bridge.py --test
python tools\relay\bambu_p1s_bridge.py --test-ftp
```

- The first should end with a printer report: state, temperatures.
- The second should end with `FTPS TEST OK`. It only lists the printer's
  storage and prints nothing.

If either fails, send me the last few lines of its output.

## 6. Start it automatically when the laptop turns on

1. Start → type **Task Scheduler** → open it → **Create Task…** (right side).
2. **General** tab:
   - Name: `Frank printer bridge`.
   - Tick **Run whether user is logged on or not**.
   - Tick **Run with highest privileges**.
3. **Triggers** tab → **New…** → Begin the task: **At startup** → OK.
4. **Actions** tab → **New…**:
   - Program: browse to `Etsy\tools\relay\start_bridge.bat` in your user
     folder.
   - "Start in": the `Etsy` folder itself, for example `C:\Users\Scott\Etsy`.
   - OK.
5. **Conditions** tab: **untick** "Start the task only if the computer is on
   AC power".
6. **Settings** tab:
   - **Untick** "Stop the task if it runs longer than".
   - Tick "If the task fails, restart every 1 minute".
7. OK, and enter your Windows password when asked.

Restart the laptop to check it works. Within a minute or two, the printer card
on Frank's Home screen should show the printer live, with no "bridge offline".
You can check that from your phone.

## What it does from then on

- **It restarts itself:** `start_bridge.bat` runs the bridge in a loop, so if
  it stops, it starts again 15 seconds later.
- **It updates itself:** before each start it runs `git pull`, so fixes reach
  the laptop without you touching it. A reboot (or Windows Update) applies
  them.
- **It works with the lid closed and the screen off.** It stops only if the
  laptop loses power or its network.

## Mac

The same steps, with these changes:

- Python and Git: python.org and `xcode-select --install`.
- Edit the file with `nano tools/relay/.env`.
- Run the tests with `python3` instead of `python`.
- Start-up: `tools/relay/start_bridge.sh` from a Login Item (System Settings →
  General → Login Items).
- Never sleep: System Settings → Battery → Options → "Prevent automatic
  sleeping when the display is off".
