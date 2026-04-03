import { mkdir, readFile, writeFile } from 'fs/promises'
import { join } from 'path'
import { app, BrowserWindow, ipcMain } from 'electron'

export interface AppSettings {
  apiBaseUrl: string
  lastSelectedSessionId: number | null
}

const defaultSettings = (): AppSettings => ({
  apiBaseUrl: 'http://127.0.0.1:8000',
  lastSelectedSessionId: null,
})

function settingsPath(): string {
  return join(app.getPath('userData'), 'delta-engineer-settings.json')
}

async function loadSettings(): Promise<AppSettings> {
  const path = settingsPath()
  try {
    const raw = await readFile(path, 'utf-8')
    const parsed = JSON.parse(raw) as Partial<AppSettings>
    return { ...defaultSettings(), ...parsed }
  } catch {
    return defaultSettings()
  }
}

async function saveSettings(partial: Partial<AppSettings>): Promise<AppSettings> {
  const path = settingsPath()
  await mkdir(app.getPath('userData'), { recursive: true })
  const next = { ...(await loadSettings()), ...partial }
  await writeFile(path, JSON.stringify(next, null, 2), 'utf-8')
  return next
}

function createWindow(): void {
  const mainWindow = new BrowserWindow({
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
      sandbox: true,
    },
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  if (process.env['ELECTRON_RENDERER_URL']) {
    void mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    void mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  ipcMain.handle('delta:get-settings', () => loadSettings())
  ipcMain.handle('delta:set-settings', (_event, partial: Partial<AppSettings>) =>
    saveSettings(partial),
  )

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
