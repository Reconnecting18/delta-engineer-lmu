import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

export type SettingsContextValue = {
  loaded: boolean
  apiBaseUrl: string
  lastSelectedSessionId: number | null
  setApiBaseUrl: (url: string) => Promise<void>
  setLastSelectedSessionId: (id: number | null) => Promise<void>
}

const SettingsContext = createContext<SettingsContextValue | null>(null)

export function SettingsProvider({ children }: { children: ReactNode }): JSX.Element {
  const [loaded, setLoaded] = useState(false)
  const [apiBaseUrl, setApiBaseUrlState] = useState('http://127.0.0.1:8000')
  const [lastSelectedSessionId, setLastSelectedSessionIdState] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false
    void window.delta.getSettings().then((s) => {
      if (cancelled) {
        return
      }
      setApiBaseUrlState(s.apiBaseUrl)
      setLastSelectedSessionIdState(s.lastSelectedSessionId)
      setLoaded(true)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const setApiBaseUrl = useCallback(async (url: string) => {
    const s = await window.delta.setSettings({ apiBaseUrl: url })
    setApiBaseUrlState(s.apiBaseUrl)
  }, [])

  const setLastSelectedSessionId = useCallback(async (id: number | null) => {
    const s = await window.delta.setSettings({ lastSelectedSessionId: id })
    setLastSelectedSessionIdState(s.lastSelectedSessionId)
  }, [])

  const value = useMemo(
    () => ({
      loaded,
      apiBaseUrl,
      lastSelectedSessionId,
      setApiBaseUrl,
      setLastSelectedSessionId,
    }),
    [loaded, apiBaseUrl, lastSelectedSessionId, setApiBaseUrl, setLastSelectedSessionId],
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
