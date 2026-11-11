import { useEffect, useRef } from "react"
import { env } from "@/lib/env"
import { docflowApi } from "@/lib/mock-api"
import type { MediaItem } from "@/lib/types"

export interface MediaJobEventPayload {
  mediaId: string
  status: MediaItem["status"]
  progressPercent: number
  errorMessage?: string
}

export interface UseMediaRealtimeOptions {
  media: MediaItem[]
  institutionId: string
  pollIntervalMs?: number
  enableSse?: boolean
  onRefresh: () => void
  onCompleted?: (completedTitles: string[]) => void
}

/**
 * Acompanha o processamento assíncrono de mídias em tempo real (`RF-09`, `FE-07`).
 * Suporta Server-Sent Events (`EventSource` em `/api/v1/jobs/{jobId}/events`)
 * com fallback automático por polling.
 */
export function useMediaRealtime({
  media,
  institutionId,
  pollIntervalMs = 2500,
  enableSse = false,
  onRefresh,
  onCompleted,
}: UseMediaRealtimeOptions): { hasActiveJobs: boolean } {
  const onRefreshRef = useRef(onRefresh)
  onRefreshRef.current = onRefresh
  const onCompletedRef = useRef(onCompleted)
  onCompletedRef.current = onCompleted

  const activeJobs = media.filter(
    (item) => item.status === "Na fila" || item.status === "Em processamento",
  )
  const hasActiveJobs = activeJobs.length > 0

  useEffect(() => {
    if (!hasActiveJobs) return

    let eventSource: EventSource | null = null
    const firstJobId = activeJobs[0]?.jobId

    if (enableSse && typeof EventSource !== "undefined" && firstJobId) {
      try {
        eventSource = new EventSource(
          `${env.apiBaseUrl}/jobs/${firstJobId}/events`,
        )
        eventSource.onmessage = () => {
          onRefreshRef.current()
        }
      } catch {
        eventSource = null
      }
    }

    const timer = window.setInterval(() => {
      const completed = docflowApi.advanceProcessingMedia(institutionId)
      onRefreshRef.current()
      if (completed.length > 0) {
        onCompletedRef.current?.(completed)
      }
    }, pollIntervalMs)

    return () => {
      window.clearInterval(timer)
      eventSource?.close()
    }
  }, [activeJobs, enableSse, hasActiveJobs, institutionId, pollIntervalMs])

  return { hasActiveJobs }
}
