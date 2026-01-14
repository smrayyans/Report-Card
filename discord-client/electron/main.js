import { app, BrowserWindow, ipcMain, shell } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import updaterPkg from 'electron-updater';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let pythonServer = null;
let mainWindow = null;

const isDev = process.env.VITE_DEV_SERVER_URL;

const ROOT_DIR = path.resolve(__dirname, '..', '..');
const PYTHON_ENTRY = path.join(ROOT_DIR, 'backend', 'app.py');
const BACKEND_EXE = path.join(process.resourcesPath, 'backend', 'report-backend.exe');
const SHOULD_START_BACKEND = process.env.FAIZAN_START_BACKEND !== '0';
const HEALTH_URL = 'http://127.0.0.1:8000/health';
const SETTINGS_DIR = app.isPackaged ? app.getPath('userData') : path.join(ROOT_DIR, 'settings');
const DB_CONFIG = path.join(SETTINGS_DIR, 'db_config.json');
const DEFAULT_OUTPUT_DIR = app.isPackaged ? path.join(SETTINGS_DIR, 'output') : path.join(ROOT_DIR, 'output');
const CONNECTION_CONFIG = path.join(SETTINGS_DIR, 'connection_config.json');

const getConfiguredOutputDir = () => {
  try {
    if (!fs.existsSync(DB_CONFIG)) {
      return null;
    }
    const raw = fs.readFileSync(DB_CONFIG, 'utf-8');
    const data = JSON.parse(raw);
    const outputDir = typeof data?.output_dir === 'string' ? data.output_dir.trim() : '';
    return outputDir || null;
  } catch (error) {
    return null;
  }
};

const getOutputDir = () => {
  return getConfiguredOutputDir() || DEFAULT_OUTPUT_DIR;
};

function startPythonServer() {
  if (!SHOULD_START_BACKEND) return;
  if (pythonServer) return;
  const env = {
    ...process.env,
    PYTHONPATH: `${process.env.PYTHONPATH ? `${process.env.PYTHONPATH}${path.delimiter}` : ''}${ROOT_DIR}`,
    FAIZAN_BASE_DIR: app.isPackaged ? process.resourcesPath : ROOT_DIR,
    FAIZAN_DB_CONFIG_DIR: SETTINGS_DIR,
    FAIZAN_OUTPUT_DIR: DEFAULT_OUTPUT_DIR,
  };
  if (app.isPackaged && fs.existsSync(BACKEND_EXE)) {
    pythonServer = spawn(BACKEND_EXE, [], { stdio: 'inherit', shell: false, env });
  } else {
    pythonServer = spawn('python', [PYTHON_ENTRY], {
      cwd: ROOT_DIR,
      stdio: 'inherit',
      shell: false,
      env,
    });
  }
  pythonServer.on('close', () => {
    pythonServer = null;
  });
}

const waitForBackend = async () => {
  if (!SHOULD_START_BACKEND || isDev || typeof fetch !== 'function') {
    return;
  }
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      const response = await fetch(HEALTH_URL, { method: 'GET' });
      if (response.ok) {
        return;
      }
    } catch (_error) {
      // Ignore until backend is ready.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
};

const broadcastWindowState = () => {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  const state = mainWindow.isMaximized() ? 'maximized' : 'normal';
  const contents = mainWindow.webContents;
  if (!contents || contents.isDestroyed()) return;
  contents.send('window-state', state);
};

const { autoUpdater } = updaterPkg;

const sendUpdateStatus = (status, payload = {}) => {
  if (!mainWindow) return;
  mainWindow.webContents.send('update-status', { status, ...payload });
};

const wireAutoUpdater = () => {
  autoUpdater.autoDownload = true;

  autoUpdater.on('checking-for-update', () => {
    sendUpdateStatus('checking');
  });

  autoUpdater.on('update-available', (info) => {
    sendUpdateStatus('available', { info });
  });

  autoUpdater.on('update-not-available', () => {
    sendUpdateStatus('not-available');
  });

  autoUpdater.on('error', (error) => {
    sendUpdateStatus('error', { message: error?.message || 'Update error' });
  });

  autoUpdater.on('download-progress', (progress) => {
    sendUpdateStatus('downloading', { progress });
  });

  autoUpdater.on('update-downloaded', () => {
    sendUpdateStatus('ready');
  });
};

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1200,
    minHeight: 720,
    backgroundColor: '#1f2128',
    frame: false,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'hidden',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false,
  });

  mainWindow.setMenuBarVisibility(false);

  mainWindow.once('ready-to-show', () => {
    if (!mainWindow) {
      return;
    }
    mainWindow.maximize();
    mainWindow.show();
    broadcastWindowState();
  });

  mainWindow.on('maximize', broadcastWindowState);
  mainWindow.on('unmaximize', broadcastWindowState);
  mainWindow.on('enter-full-screen', () => mainWindow?.webContents.send('window-state', 'maximized'));
  mainWindow.on('leave-full-screen', broadcastWindowState);

  if (isDev) {
    await mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    const indexHtml = path.join(app.getAppPath(), 'dist', 'index.html');
    await mainWindow.loadFile(indexHtml);
  }
}

ipcMain.on('window-control', (_event, action) => {
  if (!mainWindow) return;
  switch (action) {
    case 'minimize':
      mainWindow.minimize();
      break;
    case 'maximize':
      if (mainWindow.isMaximized()) {
        mainWindow.unmaximize();
      } else {
        mainWindow.maximize();
      }
      break;
    case 'close':
      mainWindow.close();
      break;
    default:
      break;
  }
  setTimeout(broadcastWindowState, 50);
});

ipcMain.handle('window-query-state', () => {
  if (!mainWindow) return 'normal';
  return mainWindow.isMaximized() ? 'maximized' : 'normal';
});

ipcMain.handle('update-check', () => {
  if (!isDev) {
    return autoUpdater.checkForUpdates();
  }
  return null;
});

ipcMain.handle('update-install', () => {
  autoUpdater.quitAndInstall();
});

ipcMain.handle('open-output-folder', async () => {
  const outputDir = getOutputDir();
  fs.mkdirSync(outputDir, { recursive: true });
  return shell.openPath(outputDir);
});

ipcMain.handle('get-connection-config', () => {
  try {
    if (!fs.existsSync(CONNECTION_CONFIG)) {
      return null;
    }
    const raw = fs.readFileSync(CONNECTION_CONFIG, 'utf-8');
    return JSON.parse(raw);
  } catch (error) {
    return { error: error?.message || 'Unable to read connection config.' };
  }
});

ipcMain.handle('save-connection-config', (_event, payload) => {
  try {
    fs.mkdirSync(SETTINGS_DIR, { recursive: true });
    fs.writeFileSync(CONNECTION_CONFIG, JSON.stringify(payload, null, 2), 'utf-8');
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error?.message || 'Unable to save connection config.' };
  }
});

app.whenReady().then(() => {
  startPythonServer();
  waitForBackend().finally(() => {
    createWindow();
  });
  if (!isDev) {
    wireAutoUpdater();
    autoUpdater.checkForUpdatesAndNotify();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (pythonServer) {
    pythonServer.kill();
  }
});
