import { useEffect, useState, type FormEvent } from 'react'

type Props = {
  open: boolean
  initialUrl: string
  initialMinimizeToTray: boolean
  showTrayPreference: boolean
  onClose: () => void
  onSave: (url: string) => Promise<void>
  onSaveMinimizeToTray: (value: boolean) => Promise<void>
}

export function ApiSettingsModal({
  open,
  initialUrl,
  initialMinimizeToTray,
  showTrayPreference,
  onClose,
  onSave,
  onSaveMinimizeToTray,
}: Props): JSX.Element | null {
  const [url, setUrl] = useState(initialUrl)
  const [minimizeToTray, setMinimizeToTray] = useState(initialMinimizeToTray)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setUrl(initialUrl)
      setMinimizeToTray(initialMinimizeToTray)
      setError(null)
    }
  }, [open, initialUrl, initialMinimizeToTray])

  if (!open) {
    return null
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      const trimmed = url.trim()
      if (!trimmed) {
        throw new Error('URL is required')
      }
      new URL(trimmed)
      await onSave(trimmed)
      if (showTrayPreference) {
        await onSaveMinimizeToTray(minimizeToTray)
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid URL')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-labelledby="settings-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="settings-title">Settings</h2>
        <form onSubmit={(e) => void handleSubmit(e)}>
          <h3 className="modal-section-title">API connection</h3>
          <p className="modal-hint">Delta Engineer API base URL (running uvicorn).</p>
          <label htmlFor="api-url">Base URL</label>
          <input
            id="api-url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="http://127.0.0.1:8000"
            autoComplete="off"
            spellCheck={false}
          />
          {showTrayPreference ? (
            <>
              <h3 className="modal-section-title">Application</h3>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={minimizeToTray}
                  onChange={(e) => setMinimizeToTray(e.target.checked)}
                />
                <span>Minimize to system tray when closing the window</span>
              </label>
            </>
          ) : null}
          {error ? <p className="error-text">{error}</p> : null}
          <div className="modal-actions">
            <button type="button" className="btn secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn primary" disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
