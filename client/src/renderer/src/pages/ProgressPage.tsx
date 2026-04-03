export function ProgressPage(): JSX.Element {
  const placeholders = [
    { label: 'Wins', value: '—' },
    { label: 'Podiums', value: '—' },
    { label: 'Races / sessions', value: '—' },
    { label: 'Driver rating trend', value: '—' },
    { label: 'Safety rating trend', value: '—' },
  ] as const

  return (
    <div className="page progress-page">
      <h1>Progress</h1>
      <p className="page-lead">
        Long-term stats and achievements as you improve. Aggregates will populate when the API exposes career-style
        metrics and history.
      </p>

      <div className="progress-grid" role="list">
        {placeholders.map(({ label, value }) => (
          <div key={label} className="home-card home-card-glow progress-card" role="listitem">
            <h2 className="home-card-title">{label}</h2>
            <p className="home-card-value">{value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
