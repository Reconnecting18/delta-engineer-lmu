import { contextBridge, ipcRenderer } from 'electron'

import type { AppSettings } from '@shared/app-settings'
import type { CaptureStatusPayload } from '@shared/capture-types'

const delta = {
  getSettings: (): Promise<AppSettings> => ipcRenderer.invoke('delta:get-settings'),
  setSettings: (partial: Partial<AppSettings>): Promise<AppSettings> =>
    ipcRenderer.invoke('delta:set-settings', partial),

  getCaptureStatus: (): Promise<CaptureStatusPayload> =>
    ipcRenderer.invoke('delta:get-capture-status'),
  startCapture: (opts: {
    apiBaseUrl: string
    autoSession: boolean
    sessionId?: number | null
  }): Promise<{ ok: boolean; error?: string }> =>
    ipcRenderer.invoke('delta:start-capture', opts),
  stopCapture: (): Promise<void> => ipcRenderer.invoke('delta:stop-capture'),
  onCaptureStatus: (cb: (status: CaptureStatusPayload) => void): (() => void) => {
    const handler = (_event: unknown, payload: CaptureStatusPayload): void => {
      cb(payload)
    }
    ipcRenderer.on('capture:status', handler)
    return () => {
      ipcRenderer.removeListener('capture:status', handler)
    }
  },
}

contextBridge.exposeInMainWorld('delta', delta)
