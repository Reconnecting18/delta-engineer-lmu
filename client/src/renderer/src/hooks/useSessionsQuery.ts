import { useQuery } from '@tanstack/react-query'
import { fetchSessions } from '@renderer/lib/api'
import { useSettings } from '@renderer/context/SettingsContext'

export function useSessionsQuery(page = 1, limit = 50) {
  const { apiBaseUrl, loaded } = useSettings()
  return useQuery({
    queryKey: ['sessions', apiBaseUrl, page, limit],
    queryFn: () => fetchSessions(apiBaseUrl, page, limit),
    enabled: loaded && Boolean(apiBaseUrl),
  })
}
