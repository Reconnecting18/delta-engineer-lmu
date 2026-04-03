import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '@renderer/components/AppShell'
import { LapsIndexPage } from '@renderer/pages/LapsIndexPage'
import { PlaceholderPage } from '@renderer/pages/PlaceholderPage'
import { SessionLapsPage } from '@renderer/pages/SessionLapsPage'
import { SessionsPage } from '@renderer/pages/SessionsPage'

export default function App(): JSX.Element {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Navigate to="/sessions" replace />} />
          <Route path="sessions" element={<SessionsPage />} />
          <Route path="sessions/:sessionId/laps" element={<SessionLapsPage />} />
          <Route path="laps" element={<LapsIndexPage />} />
          <Route
            path="live"
            element={
              <PlaceholderPage
                title="Live telemetry"
                description="Real-time dashboard fed from LMU capture (IPC) and POST /telemetry."
              />
            }
          />
          <Route
            path="setups"
            element={
              <PlaceholderPage title="Setups" description="Setup library when POST/GET /setups ships (Milestone 4)." />
            }
          />
          <Route
            path="alerts"
            element={
              <PlaceholderPage title="Alerts" description="Alert feed when GET /alerts and WS /ws/alerts ship (Milestone 5)." />
            }
          />
        </Route>
      </Routes>
    </HashRouter>
  )
}
