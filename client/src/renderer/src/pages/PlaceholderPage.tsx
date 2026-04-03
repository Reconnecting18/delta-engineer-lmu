type Props = {
  title: string
  description: string
}

export function PlaceholderPage({ title, description }: Props): JSX.Element {
  return (
    <div className="page">
      <h1>{title}</h1>
      <p className="page-lead">{description}</p>
      <p className="muted">Planned in later milestones — see docs/ui-architecture.md.</p>
    </div>
  )
}
