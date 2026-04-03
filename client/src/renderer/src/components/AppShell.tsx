import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useHealthQuery } from '@renderer/hooks/useHealthQuery'
import { useSettings } from '@renderer/context/SettingsContext'
import { ApiSettingsModal } from './ApiSettingsModal'

const nav = [
  { to: '/', label: 'Home', end: true },
  { to: '/sessions', label: 'Sessions' },
  { to: '/live', label: 'Live capture' },
  { to: '/coach', label: 'Coach' },
  { to: '/progress', label: 'Progress' },
] as const

export function AppShell(): JSX.Element {
  const { data, isError, isFetching } = useHealthQuery()
  const {
    loaded,
    ipcAvailable,
    apiBaseUrl,
    minimizeToTray,
    setApiBaseUrl,
    setMinimizeToTray,
  } = useSettings()
  const [settingsOpen, setSettingsOpen] = useState(false)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">Delta Engineer</div>
        <nav className="sidebar-nav">
          {nav.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="main-column">
        <header className="top-bar">
          <div className="top-bar-spacer" />
          {loaded && !ipcAvailable ? (
            <p className="ipc-warning" role="status">
              Preload IPC unavailable — settings use browser storage only. Restart the app after an update.
            </p>
          ) : null}
          <button
            type="button"
            className={`api-pill ${isError ? 'error' : data ? 'ok' : ''}`}
            onClick={() => setSettingsOpen(true)}
            title="Settings"
          >
            API {isFetching ? '…' : isError ? 'offline' : data ? `v${data.version}` : '—'}
          </button>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
      <ApiSettingsModal
        open={settingsOpen}
        initialUrl={apiBaseUrl}
        initialMinimizeToTray={minimizeToTray}
        showTrayPreference={ipcAvailable}
        onClose={() => setSettingsOpen(false)}
        onSave={setApiBaseUrl}
        onSaveMinimizeToTray={setMinimizeToTray}
      />
    </div>
  )
}
