export type CaptureTickMeta = {
  apiSessionId?: number
  trackName?: string
  sessionType?: string
  gamePhase?: number
  currentEt?: number
  endEt?: number
  maxLaps?: number
  captureMode?: 'manual' | 'auto'
}

/** Unified capture status (all states use the same shape for simpler React handling). */
export type CaptureStatusPayload = {
  state: 'idle' | 'starting' | 'running' | 'error'
  lastError: string | null
  ticksPosted: number
  /** API session id when known (manual target or last auto-ingest receipt). */
  sessionId: number | null
  autoSession: boolean
  pid?: number
  /** Present when state === 'error' */
  message?: string
  lastTickMeta: CaptureTickMeta | null
}
