import type { HealthResponse, LapSummaryResponse, PaginatedResponse, SessionResponse } from './api-types'

function normalizeBase(url: string): string {
  return url.replace(/\/+$/, '')
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function fetchHealth(baseUrl: string): Promise<HealthResponse> {
  const res = await fetch(`${normalizeBase(baseUrl)}/health`)
  return parseJson<HealthResponse>(res)
}

export async function fetchSessions(
  baseUrl: string,
  page = 1,
  limit = 50,
): Promise<PaginatedResponse<SessionResponse>> {
  const u = new URL('/sessions/', normalizeBase(baseUrl))
  u.searchParams.set('page', String(page))
  u.searchParams.set('limit', String(limit))
  const res = await fetch(u.toString())
  return parseJson<PaginatedResponse<SessionResponse>>(res)
}

export async function fetchSessionLaps(
  baseUrl: string,
  sessionId: number,
  page = 1,
  limit = 100,
  validOnly = false,
): Promise<PaginatedResponse<LapSummaryResponse>> {
  const u = new URL(`/sessions/${sessionId}/laps`, `${normalizeBase(baseUrl)}/`)
  u.searchParams.set('page', String(page))
  u.searchParams.set('limit', String(limit))
  if (validOnly) {
    u.searchParams.set('valid_only', 'true')
  }
  const res = await fetch(u.toString())
  return parseJson<PaginatedResponse<LapSummaryResponse>>(res)
}
