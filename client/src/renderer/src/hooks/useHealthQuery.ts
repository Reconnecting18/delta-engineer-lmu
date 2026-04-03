import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '@renderer/lib/api'
import { useSettings } from '@renderer/context/SettingsContext'

export function useHealthQuery() {
  const { apiBaseUrl, loaded } = useSettings()
  return useQuery({
    queryKey: ['health', apiBaseUrl],
    queryFn: () => fetchHealth(apiBaseUrl),
    enabled: loaded && Boolean(apiBaseUrl),
    refetchInterval: 15_000,
    retry: 1,
  })
}
