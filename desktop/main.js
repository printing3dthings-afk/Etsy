// Frank desktop shell -- spawns the bundled Python/FastAPI backend as a child
// process, waits for it to come up, then loads it into a native window (no
// address bar/tabs -- that's just what a plain Electron BrowserWindow already is,
// nothing extra needed to get the "real app, not a browser tab" feel).
//
// First launch: auto-generates <userData>/.env with a random APP_SECRET_TOKEN and a
// DB_PATH pointing inside the same app-data directory -- never inside the installed
// app bundle itself (that directory isn't reliably writable, and its contents don't
// survive an app update/reinstall). Anthropic/Etsy keys are deliberately NOT required
// for this step: the backend already degrades gracefully without them (see main.py's
// existing dependency-health pattern), so Scott can add those afterward via either the
// app's own Settings screen or the "Edit API Keys..." menu item below, which just
// opens the .env file in the OS's default text editor.
//
// Every launch re-reads that .env file and passes its contents as real process
// environment variables to the spawned backend -- NOT relying on the backend finding
// the file itself via its own ROOT-relative .env lookup, because ROOT resolves to
// sys._MEIPASS (PyInstaller's internal bundle dir) when frozen, not this app-data
// directory (see tools/api_server/main.py's frozen-detection block + this reasoning
// verified empirically in tools/desktop/backend.spec's build/test pass).

const { app, BrowserWindow, Menu, shell, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const http = require('http');

const isDev = !app.isPackaged;
const APP_DATA_DIR = app.getPath('userData');
const ENV_PATH = path.join(APP_DATA_DIR, '.env');
const DB_PATH = path.join(APP_DATA_DIR, 'hub.db');
const DEFAULT_PORT = 8891;

let backendProcess = null;
let mainWindow = null;
let quitting = false;

function ensureEnvFile() {
  fs.mkdirSync(APP_DATA_DIR, { recursive: true });
  if (fs.existsSync(ENV_PATH)) return;
  const token = crypto.randomBytes(32).toString('hex');
  const lines = [
    '# Frank desktop app -- auto-generated on first launch. Safe to edit by hand;',
    '# restart the app afterward for changes to take effect.',
    `APP_SECRET_TOKEN=${token}`,
    `DB_PATH=${DB_PATH}`,
    `PORT=${DEFAULT_PORT}`,
    '',
    '# Add your own keys below, then restart Frank:',
    '# ANTHROPIC_API_KEY=',
    '# ETSY_CLIENT_ID=',
    '# ETSY_CLIENT_SECRET=',
    '',
  ];
  fs.writeFileSync(ENV_PATH, lines.join('\n'), { encoding: 'utf8', mode: 0o600 });
}

function readEnvFile() {
  const out = {};
  const content = fs.readFileSync(ENV_PATH, 'utf8');
  for (const rawLine of content.split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq === -1) continue;
    const key = line.slice(0, eq).trim();
    const value = line.slice(eq + 1).trim();
    if (key && value) out[key] = value;
  }
  return out;
}

function waitForHealth(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    const tryOnce = () => {
      const req = http.get({ host: '127.0.0.1', port, path: '/health', timeout: 2000 }, (res) => {
        res.resume();
        if (res.statusCode === 200) return resolve();
        retry();
      });
      req.on('error', retry);
      req.on('timeout', () => { req.destroy(); retry(); });
    };
    const retry = () => {
      if (Date.now() > deadline) return reject(new Error('backend did not become healthy in time'));
      setTimeout(tryOnce, 400);
    };
    tryOnce();
  });
}

function backendExecutablePath() {
  const platExe = process.platform === 'win32' ? 'frank-backend.exe' : 'frank-backend';
  return path.join(process.resourcesPath, 'backend', platExe);
}

function spawnBackend(env) {
  if (isDev) {
    // Dev-only path: run the Python source directly (requires a `python3` on PATH with
    // the repo's requirements.txt installed) so `npm start` works without a full
    // PyInstaller build on every iteration. End users never take this path.
    const repoRoot = path.join(__dirname, '..');
    backendProcess = spawn('python3', ['tools/api_server/main.py'], { cwd: repoRoot, env });
  } else {
    backendProcess = spawn(backendExecutablePath(), [], { env });
  }

  backendProcess.stdout.on('data', (d) => process.stdout.write(`[backend] ${d}`));
  backendProcess.stderr.on('data', (d) => process.stderr.write(`[backend] ${d}`));
  backendProcess.on('exit', (code, signal) => {
    console.log(`[backend] exited (code=${code} signal=${signal})`);
    backendProcess = null;
    if (!quitting) {
      // Unexpected crash -- restart once after a short delay rather than leaving the
      // window pointed at a dead server with no explanation.
      setTimeout(() => startBackendAndWindow(), 1500);
    }
  });
}

function killBackend() {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
}

async function startBackendAndWindow() {
  ensureEnvFile();
  const envFromFile = readEnvFile();
  const port = parseInt(envFromFile.PORT || String(DEFAULT_PORT), 10);
  const env = Object.assign({}, process.env, envFromFile);

  spawnBackend(env);

  try {
    await waitForHealth(port, 30000);
  } catch (err) {
    dialog.showErrorBox('Frank failed to start',
      `The backend didn't respond in time.\n\n${err.message}\n\nCheck the console log, or try restarting Frank.`);
    return;
  }

  if (mainWindow) {
    mainWindow.loadURL(`http://127.0.0.1:${port}/frank`);
    return;
  }

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 640,
    title: 'Frank',
    icon: path.join(__dirname, 'build', process.platform === 'win32' ? 'icon.ico' : 'icon.png'),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  mainWindow.loadURL(`http://127.0.0.1:${port}/frank`);
  mainWindow.on('closed', () => { mainWindow = null; });
}

function buildMenu() {
  const template = [
    {
      label: 'Frank',
      submenu: [
        {
          label: 'Edit API Keys...',
          click: () => {
            ensureEnvFile();
            shell.openPath(ENV_PATH);
            dialog.showMessageBox({
              type: 'info',
              message: 'Restart Frank after saving your changes for them to take effect.',
            });
          },
        },
        { type: 'separator' },
        { role: 'quit' },
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
  startBackendAndWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) startBackendAndWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  quitting = true;
  killBackend();
});
