import { ChildProcess, spawn } from 'child_process'
import { createInterface } from 'readline'
import { BrowserWindow, app } from 'electron'
import { existsSync } from 'fs'
import { join } from 'path'

import type { CaptureStatusPayload, CaptureTickMeta } from '../shared/capture-types'

export type CaptureState = 'idle' | 'starting' | 'running' | 'error'

function repoRootFromMainDir(): string {
  return join(__dirname, '..', '..', '..')
}

function resolveBridgeScriptPath(): string {
  const override = process.env['DELTA_CAPTURE_SCRIPT']
  if (override) {
    return override
  }
  if (app.isPackaged) {
    const packaged = join(process.resourcesPath, 'capture', 'lmu_capture_bridge.py')
    if (existsSync(packaged)) {
      return packaged
    }
  }
  return join(repoRootFromMainDir(), 'scripts', 'lmu_capture_bridge.py')
}

function resolvePythonExecutable(): { command: string; prefixArgs: string[] } {
  const custom = process.env['DELTA_PYTHON']
  if (custom) {
    return { command: custom, prefixArgs: [] }
  }
  if (process.platform === 'win32') {
    return { command: 'py', prefixArgs: ['-3'] }
  }
  return { command: 'python3', prefixArgs: [] }
}

let child: ChildProcess | null = null
let state: CaptureState = 'idle'
let lastError: string | null = null
let ticksPosted = 0
let activeSessionId: number | null = null
let autoSessionActive = false
let stopRequested = false
let lastTickMeta: CaptureTickMeta | null = null

function broadcastStatus(): void {
  const payload = getCaptureStatus()
  for (const win of BrowserWindow.getAllWindows()) {
    win.webContents.send('capture:status', payload)
  }
}

export function getCaptureStatus(): CaptureStatusPayload {
  if (state === 'error') {
    return {
      state: 'error',
      message: lastError ?? 'Capture failed',
      lastError,
      ticksPosted,
      sessionId: activeSessionId,
      autoSession: autoSessionActive,
      lastTickMeta,
    }
  }
  if (state === 'starting') {
    return {
      state: 'starting',
      lastError,
      ticksPosted,
      sessionId: activeSessionId,
      autoSession: autoSessionActive,
      lastTickMeta,
    }
  }
  if (state === 'running') {
    return {
      state: 'running',
      lastError,
      ticksPosted,
      sessionId: activeSessionId,
      autoSession: autoSessionActive,
      pid: child?.pid,
      lastTickMeta,
    }
  }
  return {
    state: 'idle',
    lastError,
    ticksPosted,
    sessionId: activeSessionId,
    autoSession: false,
    lastTickMeta,
  }
}

type BridgeTickMessage = {
  type?: string
  version?: number
  frames_stored?: number
  api_session_id?: number
  capture_mode?: string
  track_name?: string
  session_type?: string
  game_phase?: number
  current_et?: number
  end_et?: number
  max_laps?: number
}

export async function startCapture(options: {
  sessionId?: number | null
  apiBaseUrl: string
  autoSession: boolean
}): Promise<{ ok: boolean; error?: string }> {
  if (child) {
    return { ok: false, error: 'Capture is already running' }
  }

  if (!options.autoSession && (options.sessionId == null || options.sessionId < 1)) {
    return { ok: false, error: 'Session ID is required in manual mode' }
  }

  stopRequested = false

  const scriptPath = resolveBridgeScriptPath()
  if (!existsSync(scriptPath)) {
    const msg = `Capture script not found: ${scriptPath}`
    lastError = msg
    state = 'error'
    broadcastStatus()
    return { ok: false, error: msg }
  }

  const { command, prefixArgs } = resolvePythonExecutable()
  const args = [
    ...prefixArgs,
    scriptPath,
    '--api-base-url',
    options.apiBaseUrl,
    '--poll-interval-ms',
    '10',
  ]
  if (options.autoSession) {
    args.push('--auto')
  } else {
    args.push('--session-id', String(options.sessionId))
  }

  state = 'starting'
  autoSessionActive = options.autoSession
  activeSessionId = options.autoSession ? null : options.sessionId ?? null
  lastError = null
  ticksPosted = 0
  lastTickMeta = null
  broadcastStatus()

  try {
    child = spawn(command, args, {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PYTHONUTF8: '1',
        PYTHONIOENCODING: 'utf-8',
      },
      windowsHide: true,
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    child = null
    state = 'error'
    lastError = msg
    broadcastStatus()
    return { ok: false, error: msg }
  }

  child.on('error', (err) => {
    lastError = err.message
    state = 'error'
    broadcastStatus()
  })

  child.on('exit', (code, signal) => {
    child = null
    const userStop = stopRequested
    stopRequested = false
    autoSessionActive = false
    activeSessionId = null

    if (userStop) {
      state = 'idle'
      broadcastStatus()
      return
    }

    if (state !== 'error' && code !== 0 && code !== null) {
      lastError = `Capture process exited with code ${code}${signal ? ` (${signal})` : ''}`
      state = 'error'
    } else if (state === 'running' || state === 'starting') {
      state = 'idle'
    }
    broadcastStatus()
  })

  if (child.stdout) {
    const rl = createInterface({ input: child.stdout })
    rl.on('line', (line) => {
      const trimmed = line.trim()
      if (!trimmed) {
        return
      }
      try {
        const msg = JSON.parse(trimmed) as BridgeTickMessage
        if (msg.type === 'tick') {
          ticksPosted += 1
          lastError = null
          state = 'running'
          if (typeof msg.api_session_id === 'number') {
            activeSessionId = msg.api_session_id
          }
          lastTickMeta = {
            apiSessionId: msg.api_session_id,
            trackName: msg.track_name,
            sessionType: msg.session_type,
            gamePhase: msg.game_phase,
            currentEt: msg.current_et,
            endEt: msg.end_et,
            maxLaps: msg.max_laps,
            captureMode: msg.capture_mode === 'auto' ? 'auto' : 'manual',
          }
          broadcastStatus()
        }
      } catch {
        // ignore non-JSON lines
      }
    })
  }

  if (child.stderr) {
    const rlErr = createInterface({ input: child.stderr })
    rlErr.on('line', (line) => {
      const text = line.trim()
      if (text) {
        lastError = text
        broadcastStatus()
      }
    })
  }

  state = 'running'
  broadcastStatus()
  return { ok: true }
}

export async function stopCapture(): Promise<void> {
  stopRequested = true
  if (child) {
    child.kill()
    child = null
  }
  state = 'idle'
  activeSessionId = null
  autoSessionActive = false
  lastError = null
  lastTickMeta = null
  broadcastStatus()
}
