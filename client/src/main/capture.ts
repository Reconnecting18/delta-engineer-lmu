import { ChildProcess, spawn } from 'child_process'
import { createInterface } from 'readline'
import { BrowserWindow, app } from 'electron'
import { existsSync } from 'fs'
import { join } from 'path'

export type CaptureState = 'idle' | 'starting' | 'running' | 'error'

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

function repoRootFromMainDir(): string {
  // Dev: .../client/out/main  → repo root is three levels up
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
let stopRequested = false

function broadcastStatus(): void {
  const payload = getCaptureStatus()
  for (const win of BrowserWindow.getAllWindows()) {
    win.webContents.send('capture:status', payload)
  }
}

export function getCaptureStatus(): CaptureStatusPayload {
  if (state === 'error') {
    const message = lastError ?? 'Capture failed'
    return {
      state: 'error',
      message,
      lastError,
      ticksPosted,
    }
  }
  if (state === 'starting' && activeSessionId != null) {
    return {
      state: 'starting',
      sessionId: activeSessionId,
      lastError,
      ticksPosted,
    }
  }
  if (state === 'running' && activeSessionId != null) {
    return {
      state: 'running',
      sessionId: activeSessionId,
      pid: child?.pid,
      lastError,
      ticksPosted,
    }
  }
  return { state: 'idle', lastError, ticksPosted }
}

export async function startCapture(options: {
  sessionId: number
  apiBaseUrl: string
}): Promise<{ ok: boolean; error?: string }> {
  if (child) {
    return { ok: false, error: 'Capture is already running' }
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
    '--session-id',
    String(options.sessionId),
    '--poll-interval-ms',
    '10',
  ]

  state = 'starting'
  activeSessionId = options.sessionId
  lastError = null
  ticksPosted = 0
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
        const msg = JSON.parse(trimmed) as { type?: string }
        if (msg.type === 'tick') {
          ticksPosted += 1
          lastError = null
          state = 'running'
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
  lastError = null
  broadcastStatus()
}
