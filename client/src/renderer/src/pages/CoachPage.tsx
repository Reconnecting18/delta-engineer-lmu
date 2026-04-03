import { useId } from 'react'

export function CoachPage(): JSX.Element {
  const inputId = useId()
  const hintId = useId()

  return (
    <div className="page coach-page">
      <h1>Coach</h1>
      <p className="page-lead">
        Ask for driving tips, session debriefs, or what to practice next. In a future build, Coach will connect to your AI
        backend and optionally attach the current session while you chat.
      </p>

      <div className="coach-layout">
        <div className="coach-thread home-card-glow" role="log" aria-label="Chat messages" aria-live="polite">
          <p className="coach-empty muted">
            No messages yet. When Coach is connected, your conversation will appear here.
          </p>
        </div>

        <div className="coach-composer">
          <label htmlFor={inputId} className="sr-only">
            Message to Coach
          </label>
          <textarea
            id={inputId}
            className="coach-input"
            rows={3}
            placeholder="e.g. Where should I brake at turn 3?"
            disabled
            aria-describedby={hintId}
          />
          <p id={hintId} className="coach-hint muted">
            Messaging is disabled until the Coach service is wired up (IPC / HTTP).
          </p>
          <button type="button" className="btn primary" disabled>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
