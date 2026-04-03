import type { AppSettings } from '@shared/app-settings'

/** Used when preload IPC is unavailable (e.g. misconfigured preload path). */
const FALLBACK_KEY = 'delta-engineer-renderer-settings'

export type PersistedSettings = Pick<
  AppSettings,
  'apiBaseUrl' | 'lastSelectedSessionId' | 'minimizeToTray'
>

export const defaultPersistedSettings = (): PersistedSettings => ({
  apiBaseUrl: 'http://127.0.0.1:8000',
  lastSelectedSessionId: null,
  minimizeToTray: true,
})

export function readRendererFallback(): PersistedSettings {
  try {
    const raw = localStorage.getItem(FALLBACK_KEY)
    if (!raw) {
      return defaultPersistedSettings()
    }
    const parsed = JSON.parse(raw) as Partial<PersistedSettings>
    return { ...defaultPersistedSettings(), ...parsed }
  } catch {
    return defaultPersistedSettings()
  }
}

export function writeRendererFallback(next: PersistedSettings): void {
  localStorage.setItem(FALLBACK_KEY, JSON.stringify(next))
}

export function hasDeltaBridge(): boolean {
  return typeof window !== 'undefined' && typeof window.delta?.getSettings === 'function'
}
