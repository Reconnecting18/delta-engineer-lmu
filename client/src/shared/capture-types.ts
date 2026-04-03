export type CaptureStatusPayload =
  | { state: 'idle'; lastError: string | null; ticksPosted: number }
  | { state: 'starting'; sessionId: number; lastError: string | null; ticksPosted: number }
  | {
      state: 'running'
      sessionId: number
      pid: number | undefined
      lastError: string | null
      ticksPosted: number
    }
  | { state: 'error'; message: string; lastError: string | null; ticksPosted: number }
