export interface Source {
  source_id: string
  document_id: string
  filename: string
  file_type: string
  text: string
  score: number
  chunk_index: number
  title: string | null
  page: number | null
}

export interface AskResponse {
  answer: string
  sources: Source[]
  grounded: boolean
  trace_id: string
  timings: Record<string, number>
  rewritten: boolean
}

export interface DocumentItem {
  id: string
  filename: string
  file_type: string
  status: 'pending' | 'indexed' | 'failed' | 'missing' | 'deleted'
  chunk_count: number
  error_message: string | null
  updated_at: string
}

export interface DocumentListResponse {
  items: DocumentItem[]
  total: number
}

export interface DocumentScanSummary {
  indexed: number
  skipped: number
  failed: number
  waiting: number
  missing: number
  oversized: number
  busy: boolean
  scanned_at: string | null
}

export interface DocumentScanStatus {
  directory: string
  subdirectories: string[]
  interval_seconds: number
  scanning: boolean
  last_scan: DocumentScanSummary | null
}

export interface EvaluationMetrics {
  retrieval_hit_rate: number
  faithfulness: number
  citation_completeness: number
  latency_avg_ms: number
  latency_p95_ms: number
}

export interface EvaluationRun {
  id: string
  case_count: number
  metrics: EvaluationMetrics
  created_at: string
}

export interface HealthResponse {
  status: 'ok'
  version: string
  services: {
    llm: 'configured' | 'unconfigured'
    sqlite: 'ok' | 'unavailable'
    qdrant: 'ok' | 'unavailable'
    ollama: 'ok' | 'unavailable'
  }
}
