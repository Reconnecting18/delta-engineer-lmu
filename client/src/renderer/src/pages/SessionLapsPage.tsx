import { Link, useParams } from 'react-router-dom'
import { useSessionLapsQuery } from '@renderer/hooks/useSessionLapsQuery'
import { formatDate, formatLapTime } from '@renderer/lib/format'

export function SessionLapsPage(): JSX.Element {
  const { sessionId } = useParams<{ sessionId: string }>()
  const id = sessionId ? parseInt(sessionId, 10) : NaN
  const validId = Number.isFinite(id) ? id : null
  const { data, isLoading, isError, error } = useSessionLapsQuery(validId)

  if (!validId) {
    return (
      <div className="page">
        <p className="error-text">Invalid session id.</p>
        <Link to="/sessions">Back to sessions</Link>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <Link to="/sessions" className="back-link">
          ← Sessions
        </Link>
        <h1>Lap summaries</h1>
        <p className="page-lead">
          Session <strong>{validId}</strong> — <code>GET /sessions/{validId}/laps</code>
        </p>
      </div>
      {isLoading ? <p className="muted">Loading…</p> : null}
      {isError ? (
        <p className="error-text">{error instanceof Error ? error.message : 'Failed to load laps'}</p>
      ) : null}
      {data && data.items.length === 0 ? (
        <p className="muted">
          No lap rows yet. Run <code>POST /sessions/{validId}/laps/compute</code> from the API (or Swagger) after
          telemetry exists.
        </p>
      ) : null}
      {data && data.items.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Lap</th>
                <th>Time</th>
                <th>S1</th>
                <th>S2</th>
                <th>S3</th>
                <th>Top km/h</th>
                <th>Valid</th>
                <th>Pit</th>
                <th>Ended</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((lap) => (
                <tr key={lap.id} className={lap.is_valid ? '' : 'row-muted'}>
                  <td>{lap.lap_number}</td>
                  <td>{formatLapTime(lap.lap_time)}</td>
                  <td>{lap.sector_1_time != null ? formatLapTime(lap.sector_1_time) : '—'}</td>
                  <td>{lap.sector_2_time != null ? formatLapTime(lap.sector_2_time) : '—'}</td>
                  <td>{lap.sector_3_time != null ? formatLapTime(lap.sector_3_time) : '—'}</td>
                  <td>{lap.top_speed.toFixed(1)}</td>
                  <td>{lap.is_valid ? 'Yes' : 'No'}</td>
                  <td>{lap.is_pit_lap ? 'Yes' : '—'}</td>
                  <td>{formatDate(lap.ended_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
