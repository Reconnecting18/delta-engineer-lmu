import { useEffect, useState, type FormEvent } from 'react'

type Props = {
  open: boolean
  initialUrl: string
  onClose: () => void
  onSave: (url: string) => Promise<void>
}

export function ApiSettingsModal({ open, initialUrl, onClose, onSave }: Props): JSX.Element | null {
  const [url, setUrl] = useState(initialUrl)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setUrl(initialUrl)
      setError(null)
    }
  }, [open, initialUrl])

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
        aria-labelledby="api-settings-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="api-settings-title">API connection</h2>
        <p className="modal-hint">Delta Engineer API base URL (running uvicorn).</p>
        <form onSubmit={(e) => void handleSubmit(e)}>
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
