/// <reference types="vite/client" />

interface AppSettings {
  apiBaseUrl: string
  lastSelectedSessionId: number | null
}

declare global {
  interface Window {
    delta: {
      getSettings: () => Promise<AppSettings>
      setSettings: (partial: Partial<AppSettings>) => Promise<AppSettings>
    }
  }
}

export {}
