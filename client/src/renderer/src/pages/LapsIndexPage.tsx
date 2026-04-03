import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSettings } from '@renderer/context/SettingsContext'

/** Deep link or legacy `/laps` URL: jump to last session laps or prompt user. */
export function LapsIndexPage(): JSX.Element {
  const navigate = useNavigate()
  const { lastSelectedSessionId, loaded } = useSettings()

  useEffect(() => {
    if (!loaded) {
      return
    }
    if (lastSelectedSessionId != null) {
      void navigate(`/sessions/${lastSelectedSessionId}/laps`, { replace: true })
    }
  }, [loaded, lastSelectedSessionId, navigate])

  if (!loaded) {
    return (
      <div className="page">
        <p className="muted">Loading…</p>
      </div>
    )
  }

  if (lastSelectedSessionId != null) {
    return (
      <div className="page">
        <p className="muted">Opening lap summaries…</p>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>Laps</h1>
      <p className="page-lead">Choose a session to view lap summaries.</p>
      <p>
        <Link to="/sessions">Go to sessions</Link>
      </p>
    </div>
  )
}
