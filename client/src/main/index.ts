import { existsSync } from 'fs'
import { mkdir, readFile, writeFile } from 'fs/promises'
import { join } from 'path'
import { app, BrowserWindow, ipcMain, Menu, Tray } from 'electron'

import { getCaptureStatus, startCapture, stopCapture } from './capture'
import { defaultAppSettings, type AppSettings } from '@shared/app-settings'

export type { AppSettings }

let mainWindow: BrowserWindow | null = null
let tray: Tray | null = null
let isQuitting = false
/** Kept in sync with disk settings; updated on startup and when the renderer saves preferences. */
let minimizeToTrayCached = defaultAppSettings().minimizeToTray

function settingsPath(): string {
  return join(app.getPath('userData'), 'delta-engineer-settings.json')
}

async function loadSettings(): Promise<AppSettings> {
  const path = settingsPath()
  try {
    const raw = await readFile(path, 'utf-8')
    const parsed = JSON.parse(raw) as Partial<AppSettings>
    return { ...defaultAppSettings(), ...parsed }
  } catch {
    return defaultAppSettings()
  }
}

async function saveSettings(partial: Partial<AppSettings>): Promise<AppSettings> {
  const path = settingsPath()
  await mkdir(app.getPath('userData'), { recursive: true })
  const next = { ...(await loadSettings()), ...partial }
  await writeFile(path, JSON.stringify(next, null, 2), 'utf-8')
  return next
}

function trayIconPath(): string {
  if (app.isPackaged) {
    return join(app.getAppPath(), 'assets', 'tray-icon.png')
  }
  return join(__dirname, '../../assets/tray-icon.png')
}

function createTray(): void {
  if (tray) {
    return
  }
  const iconPath = trayIconPath()
  if (!existsSync(iconPath)) {
    console.warn(`Tray icon not found at ${iconPath}; tray disabled`)
    return
  }
  tray = new Tray(iconPath)
  tray.setToolTip('E3N')
  tray.setContextMenu(
    Menu.buildFromTemplate([
      {
        label: 'Open E3N',
        click: () => {
          const win =
            mainWindow && !mainWindow.isDestroyed() ? mainWindow : BrowserWindow.getAllWindows()[0]
          win?.show()
          win?.focus()
        },
      },
      { type: 'separator' },
      {
        label: 'Quit',
        click: () => {
          isQuitting = true
          app.quit()
        },
      },
    ]),
  )
  tray.on('double-click', () => {
    const win =
      mainWindow && !mainWindow.isDestroyed() ? mainWindow : BrowserWindow.getAllWindows()[0]
    win?.show()
    win?.focus()
  })
}

async function maybeShowTrayMinimizeHint(): Promise<void> {
  if (process.platform !== 'win32' || !tray) {
    return
  }
  const settings = await loadSettings()
  if (settings.trayMinimizeHintShown) {
    return
  }
  tray.displayBalloon({
    title: 'E3N',
    content: 'E3N is still running in the background. Right-click the tray icon to quit.',
  })
  await saveSettings({ trayMinimizeHintShown: true })
}

function createMainWindow(): BrowserWindow {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.mjs'),
      contextIsolation: true,
      nodeIntegration: false,
      // sandbox: true breaks preload/contextBridge reliably on some Windows + ESM setups (blank window).
      sandbox: false,
    },
  })

  win.on('ready-to-show', () => {
    win.show()
  })

  win.on('close', (e) => {
    if (isQuitting || !minimizeToTrayCached || !tray) {
      return
    }
    e.preventDefault()
    void maybeShowTrayMinimizeHint()
    win.hide()
  })

  if (process.env['ELECTRON_RENDERER_URL']) {
    void win.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    void win.loadFile(join(__dirname, '../renderer/index.html'))
  }

  return win
}

app.whenReady().then(async () => {
  const initial = await loadSettings()
  minimizeToTrayCached = initial.minimizeToTray

  ipcMain.handle('delta:get-settings', () => loadSettings())
  ipcMain.handle('delta:set-settings', async (_event, partial: Partial<AppSettings>) => {
    const next = await saveSettings(partial)
    if (typeof partial.minimizeToTray === 'boolean') {
      minimizeToTrayCached = next.minimizeToTray
    }
    return next
  })

  ipcMain.handle('delta:get-capture-status', () => getCaptureStatus())
  ipcMain.handle(
    'delta:start-capture',
    async (_event, opts: { sessionId: number; apiBaseUrl: string }) => startCapture(opts),
  )
  ipcMain.handle('delta:stop-capture', () => stopCapture())

  mainWindow = createMainWindow()
  createTray()

  app.on('activate', () => {
    const win = mainWindow && !mainWindow.isDestroyed() ? mainWindow : null
    if (win) {
      win.show()
      return
    }
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow()
    }
  })
})

app.on('before-quit', () => {
  isQuitting = true
  void stopCapture()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
