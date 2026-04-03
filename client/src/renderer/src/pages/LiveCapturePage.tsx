import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { useCaptureStatus } from '@renderer/hooks/useCaptureStatus'
import { useSettings } from '@renderer/context/SettingsContext'
import { hasDeltaBridge } from '@renderer/lib/settings-storage'

export function LiveCapturePage(): JSX.Element {
  const { apiBaseUrl, lastSelectedSessionId, setLastSelectedSessionId, loaded, ipcAvailable } =
    useSettings()
  const captureStatus = useCaptureStatus()
  const [sessionInput, setSessionInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  useEffect(() => {
    if (lastSelectedSessionId != null) {
      setSessionInput(String(lastSelectedSessionId))
    }
  }, [lastSelectedSessionId])

  const bridgeOk = hasDeltaBridge() && ipcAvailable

  const handleStart = async (e: FormEvent): Promise<void> => {
    e.preventDefault()
    setLocalError(null)
    const id = Number.parseInt(sessionInput.trim(), 10)
    if (!Number.isFinite(id) || id < 1) {
      setLocalError('Enter a valid session ID (positive integer).')
      return
    }
    setBusy(true)
    try {
      const result = await window.delta.startCapture({
        sessionId: id,
        apiBaseUrl,
      })
      if (!result.ok) {
        setLocalError(result.error ?? 'Failed to start capture')
      } else {
        void setLastSelectedSessionId(id)
      }
    } finally {
      setBusy(false)
    }
  }

  const handleStop = async (): Promise<void> => {
    setLocalError(null)
    setBusy(true)
    try {
      await window.delta.stopCapture()
    } finally {
      setBusy(false)
    }
  }

  const running =
    captureStatus?.state === 'running' ||
    captureStatus?.state === 'starting'

  const statusLabel = !loaded
    ? 'Loading…'
    : !bridgeOk
      ? 'Unavailable (use Electron app)'
      : captureStatus == null
        ? '…'
        : captureStatus.state === 'idle'
          ? 'Idle'
          : captureStatus.state === 'starting'
            ? 'Starting…'
            : captureStatus.state === 'running'
              ? `Running · ${captureStatus.ticksPosted} posts`
              : `Error · ${captureStatus.message}`

  return (
    <div className="page live-capture-page">
      <h1>Live capture</h1>
      <p className="page-lead">
        Stream telemetry from Le Mans Ultimate (rF2 shared memory plugin) into a session you created
        in Delta Engineer. Start the API, create a session under Sessions, then drive with LMU
        running.
      </p>

      <section className="live-capture-status" aria-label="Capture status">
        <h2 className="home-section-title">Status</h2>
        <p className="home-card-value">{statusLabel}</p>
        {captureStatus?.lastError && captureStatus.state !== 'error' ? (
          <p className="muted" role="status">
            {captureStatus.lastError}
          </p>
        ) : null}
      </section>

      <section className="live-capture-form" aria-label="Start capture">
        <h2 className="home-section-title">Session</h2>
        <form onSubmit={(e) => void handleStart(e)} className="live-capture-form-inner">
          <label htmlFor="capture-session-id">Session ID</label>
          <input
            id="capture-session-id"
            type="number"
            min={1}
            step={1}
            value={sessionInput}
            onChange={(e) => setSessionInput(e.target.value)}
            disabled={!bridgeOk || running || busy}
            className="live-capture-input"
          />
          <div className="live-capture-actions">
            <button
              type="submit"
              className="btn primary"
              disabled={!bridgeOk || running || busy}
            >
              Start capture
            </button>
            <button
              type="button"
              className="btn secondary"
              disabled={!bridgeOk || !running || busy}
              onClick={() => void handleStop()}
            >
              Stop
            </button>
          </div>
        </form>
        {localError ? (
          <p className="ipc-warning" role="alert">
            {localError}
          </p>
        ) : null}
        <p className="muted">
          API target: <strong>{apiBaseUrl}</strong> — change from the header if needed.
        </p>
      </section>

      <section className="live-capture-help" aria-label="Setup">
        <h2 className="home-section-title">LMU setup</h2>
        <ul className="home-focus-list">
          <li>
            Install and enable the rF2 Shared Memory Map plugin for LMU (see repository{' '}
            <code>README.md</code> and <code>docs/telemetry-format.md</code>).
          </li>
          <li>Windows only — shared memory capture does not run on macOS/Linux.</li>
          <li>
            Python 3.11+ on <code>PATH</code> (or set <code>DELTA_PYTHON</code> to your interpreter).
            On Windows the app tries <code>py -3</code> first.
          </li>
        </ul>
        <p>
          <Link to="/sessions" className="btn link">
            Manage sessions
          </Link>
        </p>
      </section>
    </div>
  )
}
