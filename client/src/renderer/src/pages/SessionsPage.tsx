import { useNavigate } from 'react-router-dom'
import { useSessionsQuery } from '@renderer/hooks/useSessionsQuery'
import { useSettings } from '@renderer/context/SettingsContext'
import { formatDate, formatLapTime } from '@renderer/lib/format'

export function SessionsPage(): JSX.Element {
  const navigate = useNavigate()
  const { setLastSelectedSessionId } = useSettings()
  const { data, isLoading, isError, error } = useSessionsQuery(1, 50)

  const openLaps = async (sessionId: number) => {
    await setLastSelectedSessionId(sessionId)
    void navigate(`/sessions/${sessionId}/laps`)
  }

  return (
    <div className="page">
      <h1>Sessions</h1>
      <p className="page-lead">
        Open past or current sessions and jump into lap summaries for post-run analysis — data from{' '}
        <code>GET /sessions</code>.
      </p>
      {isLoading ? <p className="muted">Loading…</p> : null}
      {isError ? (
        <p className="error-text">{error instanceof Error ? error.message : 'Failed to load sessions'}</p>
      ) : null}
      {data && data.items.length === 0 ? <p className="muted">No sessions yet. Ingest telemetry via the API first.</p> : null}
      {data && data.items.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Track</th>
                <th>Car</th>
                <th>Driver</th>
                <th>Type</th>
                <th>Started</th>
                <th>Laps</th>
                <th>Best</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.items.map((s) => (
                <tr key={s.id}>
                  <td>{s.id}</td>
                  <td>{s.track_name}</td>
                  <td>{s.car_name}</td>
                  <td>{s.driver_name}</td>
                  <td>{s.session_type}</td>
                  <td>{formatDate(s.started_at)}</td>
                  <td>{s.total_laps}</td>
                  <td>{s.best_lap_time != null ? formatLapTime(s.best_lap_time) : '—'}</td>
                  <td>
                    <button type="button" className="btn link" onClick={() => void openLaps(s.id)}>
                      Lap summaries
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
