import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { useCaptureStatus } from '@renderer/hooks/useCaptureStatus'
import { useSettings } from '@renderer/context/SettingsContext'
import { hasDeltaBridge } from '@renderer/lib/settings-storage'

export function LiveCapturePage(): JSX.Element {
  const { apiBaseUrl, lastSelectedSessionId, setLastSelectedSessionId, loaded, ipcAvailable } =
    useSettings()
  const captureStatus = useCaptureStatus()
  const [autoSession, setAutoSession] = useState(true)
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
    if (!autoSession) {
      const id = Number.parseInt(sessionInput.trim(), 10)
      if (!Number.isFinite(id) || id < 1) {
        setLocalError('Enter a valid session ID (positive integer), or enable automatic session.')
        return
      }
    }
    setBusy(true)
    try {
      const id = Number.parseInt(sessionInput.trim(), 10)
      const result = await window.delta.startCapture({
        apiBaseUrl,
        autoSession,
        sessionId: autoSession ? undefined : Number.isFinite(id) && id >= 1 ? id : undefined,
      })
      if (!result.ok) {
        setLocalError(result.error ?? 'Failed to start capture')
      } else if (!autoSession && Number.isFinite(id) && id >= 1) {
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
    captureStatus?.state === 'running' || captureStatus?.state === 'starting'

  const meta = captureStatus?.lastTickMeta
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
              ? `Running · ${captureStatus.ticksPosted} posts${
                  meta?.trackName ? ` · ${meta.trackName}` : ''
                }`
              : `Error · ${captureStatus.message ?? 'unknown'}`

  return (
    <div className="page live-capture-page">
      <h1>Live capture</h1>
      <p className="page-lead">
        Stream telemetry from Le Mans Ultimate into Delta Engineer. Use <strong>automatic session</strong>{' '}
        to create or continue API sessions from scoring data (track, car, practice/qual/race), or pick a
        fixed session ID for manual control.
      </p>

      <section className="live-capture-status" aria-label="Capture status">
        <h2 className="home-section-title">Status</h2>
        <p className="home-card-value">{statusLabel}</p>
        {captureStatus?.sessionId != null && captureStatus.state === 'running' ? (
          <p className="muted" role="status">
            API session id: <strong>{captureStatus.sessionId}</strong>
            {meta?.sessionType ? ` · ${meta.sessionType}` : ''}
            {meta?.gamePhase != null ? ` · phase ${meta.gamePhase}` : ''}
          </p>
        ) : null}
        {meta?.currentEt != null && meta.endEt != null && meta.endEt > meta.currentEt ? (
          <p className="muted" role="status">
            Session clock ~{meta.currentEt.toFixed(0)}s / end ~{meta.endEt.toFixed(0)}s (sim ET; see
            telemetry-format.md)
          </p>
        ) : null}
        {captureStatus?.lastError && captureStatus.state !== 'error' ? (
          <p className="muted" role="status">
            {captureStatus.lastError}
          </p>
        ) : null}
      </section>

      <section className="live-capture-form" aria-label="Start capture">
        <h2 className="home-section-title">Session</h2>
        <label className="live-capture-check">
          <input
            type="checkbox"
            checked={autoSession}
            onChange={(e) => setAutoSession(e.target.checked)}
            disabled={!bridgeOk || running || busy}
          />{' '}
          Automatic session (from LMU scoring — track, car, driver, session type)
        </label>
        <form onSubmit={(e) => void handleStart(e)} className="live-capture-form-inner">
          {!autoSession ? (
            <>
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
            </>
          ) : (
            <p className="muted">
              Waiting for LMU with telemetry + scoring shared memory. Sessions appear under{' '}
              <Link to="/sessions">Sessions</Link> as you drive.
            </p>
          )}
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
            Install the rF2 Shared Memory Map plugin; enable both <strong>Telemetry</strong> and{' '}
            <strong>Scoring</strong> subscriptions (automatic mode needs scoring for session context).
          </li>
          <li>Windows only — shared memory capture does not run on macOS/Linux.</li>
          <li>
            Python 3.11+ on <code>PATH</code> (or <code>DELTA_PYTHON</code>). On Windows the app tries{' '}
            <code>py -3</code> first.
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
