import { useEffect, useState } from 'react'

import type { CaptureStatusPayload } from '@shared/capture-types'

import { hasDeltaBridge } from '@renderer/lib/settings-storage'

export function useCaptureStatus(): CaptureStatusPayload | null {
  const [status, setStatus] = useState<CaptureStatusPayload | null>(null)

  useEffect(() => {
    if (!hasDeltaBridge()) {
      setStatus(null)
      return
    }

    let unsub: (() => void) | undefined

    const run = async () => {
      try {
        const initial = await window.delta.getCaptureStatus()
        setStatus(initial)
        unsub = window.delta.onCaptureStatus((next) => {
          setStatus(next)
        })
      } catch {
        setStatus(null)
      }
    }

    void run()

    return () => {
      unsub?.()
    }
  }, [])

  return status
}
