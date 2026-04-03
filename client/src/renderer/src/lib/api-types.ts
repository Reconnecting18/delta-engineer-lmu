/** Mirrors FastAPI `HealthResponse`. */
export interface HealthResponse {
  status: string
  version: string
  environment: string
}

/** Mirrors `SessionResponse` / list items. */
export interface SessionResponse {
  id: number
  track_name: string
  car_name: string
  driver_name: string
  session_type: string
  started_at: string
  ended_at: string | null
  total_laps: number
  best_lap_time: number | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
}

/** Mirrors `LapSummaryResponse`. */
export interface LapSummaryResponse {
  id: number
  session_id: number
  lap_number: number
  lap_time: number
  sector_1_time: number | null
  sector_2_time: number | null
  sector_3_time: number | null
  top_speed: number
  average_speed: number
  min_tire_temp: number | null
  max_tire_temp: number | null
  fuel_used: number
  fuel_level_start: number
  fuel_level_end: number
  is_valid: boolean
  is_pit_lap: boolean
  started_at: string
  ended_at: string
}
