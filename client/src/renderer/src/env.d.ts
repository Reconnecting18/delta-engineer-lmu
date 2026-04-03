/// <reference types="vite/client" />

import type { AppSettings } from '@shared/app-settings'
import type { CaptureStatusPayload } from '@shared/capture-types'

declare global {
  interface Window {
    delta: {
      getSettings: () => Promise<AppSettings>
      setSettings: (partial: Partial<AppSettings>) => Promise<AppSettings>
      getCaptureStatus: () => Promise<CaptureStatusPayload>
      startCapture: (opts: {
        apiBaseUrl: string
        autoSession: boolean
        sessionId?: number | null
      }) => Promise<{ ok: boolean; error?: string }>
      stopCapture: () => Promise<void>
      onCaptureStatus: (cb: (status: CaptureStatusPayload) => void) => () => void
    }
  }
}

export {}
