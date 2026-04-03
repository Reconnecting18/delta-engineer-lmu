import { useQuery } from '@tanstack/react-query'
import { fetchSessionLaps } from '@renderer/lib/api'
import { useSettings } from '@renderer/context/SettingsContext'

export function useSessionLapsQuery(sessionId: number | null) {
  const { apiBaseUrl, loaded } = useSettings()
  return useQuery({
    queryKey: ['session-laps', apiBaseUrl, sessionId],
    queryFn: () => fetchSessionLaps(apiBaseUrl, sessionId!, 1, 100, false),
    enabled: loaded && Boolean(apiBaseUrl) && sessionId != null && sessionId > 0,
  })
}
