import { Link } from 'react-router-dom'
import { useCaptureStatus } from '@renderer/hooks/useCaptureStatus'
import { useHealthQuery } from '@renderer/hooks/useHealthQuery'
import { useSessionsQuery } from '@renderer/hooks/useSessionsQuery'
import { useSettings } from '@renderer/context/SettingsContext'
import { formatDate, formatLapTime } from '@renderer/lib/format'

export function HomePage(): JSX.Element {
  const { data: health, isError, isFetching } = useHealthQuery()
  const { data: sessionsData, isLoading: sessionsLoading } = useSessionsQuery(1, 5)
  const { loaded, ipcAvailable } = useSettings()
  const captureStatus = useCaptureStatus()

  const captureSummary =
    captureStatus == null
      ? ipcAvailable
        ? 'Idle'
        : 'Browser mode'
      : captureStatus.state === 'running' || captureStatus.state === 'starting'
        ? `Active · ${captureStatus.ticksPosted} posts`
        : captureStatus.state === 'error'
          ? `Error${captureStatus.message ? ` · ${captureStatus.message}` : ''}`
          : 'Idle'

  const recent = sessionsData?.items.slice(0, 5) ?? []

  return (
    <div className="page home-page">
      <h1>Home</h1>
      <p className="page-lead">
        Quick pit-lane view: connection status, recent sessions, and shortcuts to analysis or Coach.
      </p>

      <section className="home-status-grid" aria-label="Status">
        <div className="home-card home-card-glow">
          <h2 className="home-card-title">API</h2>
          <p className="home-card-value">
            {!loaded ? '…' : isFetching ? 'Checking…' : isError ? 'Offline' : health ? `OK · v${health.version}` : 'Unknown'}
          </p>
          <p className="home-card-hint muted">Use the API pill in the header to change the base URL.</p>
        </div>
        <div className="home-card home-card-glow">
          <h2 className="home-card-title">Capture</h2>
          <p className="home-card-value">{!loaded ? '…' : captureSummary}</p>
          <p className="home-card-hint muted">
            <Link to="/live">Open Live capture</Link> to stream LMU telemetry into a session (Windows +
            Python + shared-memory plugin).
          </p>
        </div>
      </section>

      <section className="home-focus" aria-label="Suggested focus">
        <h2 className="home-section-title">Today&apos;s focus</h2>
        <ul className="home-focus-list">
          <li>Open your latest session and review lap summaries for consistency.</li>
          <li>Use Coach for specific corners or racecraft questions when it&apos;s connected.</li>
          <li>Track long-term trends under Progress as session stats accumulate.</li>
        </ul>
      </section>

      <section className="home-actions" aria-label="Shortcuts">
        <Link to="/sessions" className="btn primary home-action-btn">
          Sessions
        </Link>
        <Link to="/coach" className="btn secondary home-action-btn">
          Coach
        </Link>
        <Link to="/progress" className="btn secondary home-action-btn">
          Progress
        </Link>
      </section>

      <section className="home-recent" aria-label="Recent sessions">
        <h2 className="home-section-title">Recent sessions</h2>
        {sessionsLoading ? <p className="muted">Loading…</p> : null}
        {!sessionsLoading && recent.length === 0 ? (
          <p className="muted">No sessions yet. Ingest telemetry via the API, then open Sessions.</p>
        ) : null}
        {!sessionsLoading && recent.length > 0 ? (
          <ul className="home-recent-list">
            {recent.map((s) => (
              <li key={s.id}>
                <Link to={`/sessions/${s.id}/laps`} className="home-recent-link">
                  <span className="home-recent-main">
                    {s.track_name} · {s.car_name}
                  </span>
                  <span className="home-recent-meta muted">
                    {formatDate(s.started_at)}
                    {s.best_lap_time != null ? ` · best ${formatLapTime(s.best_lap_time)}` : ''}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : null}
        <p className="home-recent-footer">
          <Link to="/sessions" className="btn link">
            View all sessions
          </Link>
        </p>
      </section>
    </div>
  )
}
