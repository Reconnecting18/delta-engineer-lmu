/** Format seconds as `M:SS.mmm` for lap times. */
export function formatLapTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds - m * 60
  const whole = Math.floor(s)
  const frac = Math.round((s - whole) * 1000)
  const secStr = `${whole}.${String(frac).padStart(3, '0')}`
  return `${m}:${secStr.padStart(6, '0')}`
}

export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}
