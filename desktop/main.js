// Frank desktop shell -- thin client. Loads the real, live Frank dashboard
// (the same Railway deployment Scott already uses in a browser tab) into a
// native window: system tray icon, OS notifications for new alerts, and a
// global show/hide hotkey on top of it. No local backend, no local database,
// no separate copy of Scott's data -- this is a dedicated window onto the one
// real Frank, not a second instance of it.
//
// (2026-08-06, "make Frank next-level" desktop follow-up) This replaces an
// earlier version of this file that spawned a bundled PyInstaller copy of
// tools/api_server/main.py as a child process and pointed the window at
// 127.0.0.1. That local-instance model was built, worked, and shipped one
// real Windows/macOS installer via CI -- but it started with an empty local
// database (no orders, no listings, no chat history) and needed API keys
// re-entered by hand, so it was never actually a window onto Scott's real
// shop. Scott confirmed the thin-client direction explicitly ("Option a it
// is") after a pros/cons comparison. The old local-backend packaging scripts
// (tools/desktop/backend.spec, tools/desktop/build_backend.py) are archived
// via tools/trash.py rather than left as dead code -- see data/trash/
// DELETED.md for the exact entries if that model is ever needed again.
//
// Auth: Electron's default session persists cookies to disk the same way a
// real browser profile does, so Scott logs into /login once inside this
// window and stays logged in across restarts -- no separate credential
// handling needed here at all.

const { app, BrowserWindow, Tray, Menu, shell, dialog, globalShortcut, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const https = require('https');
const http = require('http');

const APP_DATA_DIR = app.getPath('userData');
const CONFIG_PATH = path.join(APP_DATA_DIR, 'config.json');
const DEFAULT_LIVE_URL = 'https://etsy-production-b2f1.up.railway.app';
const HOTKEY = 'CommandOrControl+Shift+F';

let mainWindow = null;
let tray = null;
let quitting = false;

function iconPath(name) {
  return path.join(__dirname, 'build', name);
}

function readConfig() {
  try {
    const raw = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
    if (raw && typeof raw.liveUrl === 'string' && raw.liveUrl.trim()) {
      return { liveUrl: raw.liveUrl.trim().replace(/\/+$/, '') };
    }
  } catch (_err) {
    // Missing or invalid config -- fall through to the default below. This is
    // the expected state on first launch, not an error worth surfacing.
  }
  return { liveUrl: DEFAULT_LIVE_URL };
}

function ensureConfigFile() {
  fs.mkdirSync(APP_DATA_DIR, { recursive: true });
  if (fs.existsSync(CONFIG_PATH)) return;
  const initial = { liveUrl: process.env.FRANK_DESKTOP_URL || DEFAULT_LIVE_URL };
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(initial, null, 2) + '\n', 'utf8');
}

function liveUrl() {
  // An env var override (for pointing the shell at a local dev server while
  // working on this file itself) always wins over the saved config.
  if (process.env.FRANK_DESKTOP_URL) return process.env.FRANK_DESKTOP_URL.replace(/\/+$/, '');
  return readConfig().liveUrl;
}

function checkReachable(baseUrl, timeoutMs) {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeoutMs;
    const attempt = () => {
      let url;
      try {
        url = new URL('/health', baseUrl);
      } catch (err) {
        reject(err);
        return;
      }
      const lib = url.protocol === 'http:' ? http : https;
      const req = lib.get(url, { timeout: 5000 }, (res) => {
        res.resume();
        resolve();
      });
      req.on('error', retry);
      req.on('timeout', () => { req.destroy(); retry(); });
    };
    const retry = () => {
      if (Date.now() > deadline) {
        reject(new Error(`could not reach ${baseUrl} -- check your internet connection`));
        return;
      }
      setTimeout(attempt, 1500);
    };
    attempt();
  });
}

// Injected into the live page after every navigation. Polls the SAME real
// /api/alerts endpoint that already backs the in-app notification bell (no
// separate/duplicate alert logic to keep in sync) and fires a native OS
// notification for any alert that wasn't present on the previous poll.
// Alerts have no stable ID (they're recomputed live from current conditions
// each call, see main.py's get_alerts()), so `source + '::' + title` is used
// as a synthetic dedup key -- stable across polls for the same underlying
// condition. The FIRST poll after launch/reload seeds the seen-set without
// notifying, so restarting the app never re-fires a storm of alerts for
// conditions that were already open before this window existed.
const NOTIFIER_JS = `
(function() {
  if (window.__frankDesktopNotifier) return;
  window.__frankDesktopNotifier = true;
  var seen = new Set();
  var firstPoll = true;
  function poll() {
    fetch('/api/alerts', { credentials: 'include' })
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (!d || !Array.isArray(d.alerts)) return;
        d.alerts.forEach(function(a) {
          var key = (a.source || '') + '::' + (a.title || '');
          if (seen.has(key)) return;
          seen.add(key);
          if (firstPoll) return;
          try {
            var n = new Notification(a.title || 'Frank alert', { body: a.detail || '' });
            n.onclick = function() { window.focus(); };
          } catch (_e) { /* Notification API unavailable -- skip silently */ }
        });
        firstPoll = false;
      })
      .catch(function() { /* transient network error -- next poll will retry */ });
  }
  poll();
  setInterval(poll, 60000);
})();
`;

function installNotifier() {
  if (!mainWindow) return;
  mainWindow.webContents.executeJavaScript(NOTIFIER_JS).catch((err) => {
    console.error('[desktop] failed to install alert notifier:', err.message);
  });
}

function toggleWindow() {
  if (!mainWindow) return;
  if (mainWindow.isVisible() && mainWindow.isFocused()) {
    mainWindow.hide();
  } else {
    mainWindow.show();
    mainWindow.focus();
  }
}

async function createWindow() {
  ensureConfigFile();
  const url = liveUrl();

  try {
    await checkReachable(url, 20000);
  } catch (err) {
    const choice = dialog.showMessageBoxSync({
      type: 'error',
      title: 'Frank is unreachable',
      message: `Couldn't reach Frank at ${url}.\n\n${err.message}`,
      buttons: ['Retry', 'Quit'],
      defaultId: 0,
    });
    if (choice === 0) return createWindow();
    app.quit();
    return;
  }

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 640,
    title: 'Frank',
    icon: iconPath(process.platform === 'win32' ? 'icon.ico' : 'icon.png'),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.webContents.on('did-finish-load', installNotifier);
  mainWindow.loadURL(`${url}/frank`);

  mainWindow.on('close', (event) => {
    if (quitting) return;
    // Tray-app behavior: closing the window hides it (so the alert notifier
    // keeps polling in the background) rather than quitting Frank outright.
    // Real quit is only via the tray menu, app menu, or Cmd/Ctrl+Q.
    event.preventDefault();
    mainWindow.hide();
  });
  mainWindow.on('closed', () => { mainWindow = null; });
}

function createTray() {
  const trayIcon = nativeImage.createFromPath(iconPath('icon.png')).resize({ width: 16, height: 16 });
  tray = new Tray(trayIcon);
  tray.setToolTip('Frank — OnBrandCraftz');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open Frank', click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } } },
    { type: 'separator' },
    {
      label: 'Quit Frank',
      click: () => {
        quitting = true;
        app.quit();
      },
    },
  ]));
  tray.on('click', toggleWindow);
}

function buildMenu() {
  const template = [
    {
      label: 'Frank',
      submenu: [
        {
          label: 'Change Server URL...',
          click: () => {
            ensureConfigFile();
            shell.openPath(CONFIG_PATH);
            dialog.showMessageBox({
              type: 'info',
              message: 'Edit "liveUrl", save, then restart Frank for the change to take effect.',
            });
          },
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: 'CommandOrControl+Q',
          click: () => { quitting = true; app.quit(); },
        },
      ],
    },
    { role: 'editMenu' },
    { role: 'viewMenu' },
    { role: 'windowMenu' },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.whenReady().then(() => {
  buildMenu();
  createTray();
  createWindow();

  globalShortcut.register(HOTKEY, toggleWindow);

  app.on('activate', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    } else {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Tray app: never quit just because the window closed (it's hidden, not
  // destroyed -- see the 'close' handler above). Quitting only happens via
  // the explicit paths that set `quitting = true` first.
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

app.on('before-quit', () => {
  quitting = true;
});
