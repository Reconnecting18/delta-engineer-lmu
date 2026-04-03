import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '@renderer/components/AppShell'
import { CoachPage } from '@renderer/pages/CoachPage'
import { HomePage } from '@renderer/pages/HomePage'
import { LapsIndexPage } from '@renderer/pages/LapsIndexPage'
import { ProgressPage } from '@renderer/pages/ProgressPage'
import { LiveCapturePage } from '@renderer/pages/LiveCapturePage'
import { SessionLapsPage } from '@renderer/pages/SessionLapsPage'
import { SessionsPage } from '@renderer/pages/SessionsPage'

export default function App(): JSX.Element {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="sessions" element={<SessionsPage />} />
          <Route path="sessions/:sessionId/laps" element={<SessionLapsPage />} />
          <Route path="laps" element={<LapsIndexPage />} />
          <Route path="coach" element={<CoachPage />} />
          <Route path="progress" element={<ProgressPage />} />
          <Route path="live" element={<LiveCapturePage />} />
          <Route path="setups" element={<Navigate to="/sessions" replace />} />
          <Route path="alerts" element={<Navigate to="/sessions" replace />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}
