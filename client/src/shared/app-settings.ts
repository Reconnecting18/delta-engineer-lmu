export type AppSettings = {
  apiBaseUrl: string
  lastSelectedSessionId: number | null
  /** When true, closing the main window hides to the system tray instead of quitting. */
  minimizeToTray: boolean
  /** Windows: first minimize-to-tray balloon has been shown. */
  trayMinimizeHintShown: boolean
}

export function defaultAppSettings(): AppSettings {
  return {
    apiBaseUrl: 'http://127.0.0.1:8000',
    lastSelectedSessionId: null,
    minimizeToTray: true,
    trayMinimizeHintShown: false,
  }
}
