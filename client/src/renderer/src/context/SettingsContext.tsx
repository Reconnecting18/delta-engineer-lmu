import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  hasDeltaBridge,
  readRendererFallback,
  writeRendererFallback,
} from '@renderer/lib/settings-storage'

export type SettingsContextValue = {
  loaded: boolean
  ipcAvailable: boolean
  apiBaseUrl: string
  lastSelectedSessionId: number | null
  setApiBaseUrl: (url: string) => Promise<void>
  setLastSelectedSessionId: (id: number | null) => Promise<void>
}

const SettingsContext = createContext<SettingsContextValue | null>(null)

export function SettingsProvider({ children }: { children: ReactNode }): JSX.Element {
  const [loaded, setLoaded] = useState(false)
  const [ipcAvailable, setIpcAvailable] = useState(true)
  const [apiBaseUrl, setApiBaseUrlState] = useState('http://127.0.0.1:8000')
  const [lastSelectedSessionId, setLastSelectedSessionIdState] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      if (hasDeltaBridge()) {
        try {
          const s = await window.delta.getSettings()
          if (cancelled) {
            return
          }
          setApiBaseUrlState(s.apiBaseUrl)
          setLastSelectedSessionIdState(s.lastSelectedSessionId)
          setIpcAvailable(true)
        } catch {
          if (cancelled) {
            return
          }
          const fb = readRendererFallback()
          setApiBaseUrlState(fb.apiBaseUrl)
          setLastSelectedSessionIdState(fb.lastSelectedSessionId)
          setIpcAvailable(false)
        }
      } else {
        const fb = readRendererFallback()
        if (!cancelled) {
          setApiBaseUrlState(fb.apiBaseUrl)
          setLastSelectedSessionIdState(fb.lastSelectedSessionId)
          setIpcAvailable(false)
        }
      }
      if (!cancelled) {
        setLoaded(true)
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [])

  const setApiBaseUrl = useCallback(async (url: string) => {
    if (hasDeltaBridge()) {
      const s = await window.delta.setSettings({ apiBaseUrl: url })
      setApiBaseUrlState(s.apiBaseUrl)
      return
    }
    const next = { apiBaseUrl: url, lastSelectedSessionId }
    writeRendererFallback(next)
    setApiBaseUrlState(url)
  }, [lastSelectedSessionId])

  const setLastSelectedSessionId = useCallback(async (id: number | null) => {
    if (hasDeltaBridge()) {
      const s = await window.delta.setSettings({ lastSelectedSessionId: id })
      setLastSelectedSessionIdState(s.lastSelectedSessionId)
      return
    }
    const next = { apiBaseUrl, lastSelectedSessionId: id }
    writeRendererFallback(next)
    setLastSelectedSessionIdState(id)
  }, [apiBaseUrl])

  const value = useMemo(
    () => ({
      loaded,
      ipcAvailable,
      apiBaseUrl,
      lastSelectedSessionId,
      setApiBaseUrl,
      setLastSelectedSessionId,
    }),
    [
      loaded,
      ipcAvailable,
      apiBaseUrl,
      lastSelectedSessionId,
      setApiBaseUrl,
      setLastSelectedSessionId,
    ],
  )

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext)
  if (!ctx) {
    throw new Error('useSettings must be used within SettingsProvider')
  }
  return ctx
}
