import { contextBridge, ipcRenderer } from 'electron'

export interface AppSettings {
  apiBaseUrl: string
  lastSelectedSessionId: number | null
}

const delta = {
  getSettings: (): Promise<AppSettings> => ipcRenderer.invoke('delta:get-settings'),
  setSettings: (partial: Partial<AppSettings>): Promise<AppSettings> =>
    ipcRenderer.invoke('delta:set-settings', partial),
}

contextBridge.exposeInMainWorld('delta', delta)
