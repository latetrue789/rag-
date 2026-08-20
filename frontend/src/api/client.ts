import type {
  AskResponse,
  DocumentListResponse,
  EvaluationRun,
  HealthResponse,
} from '../types'

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(body?.detail ?? '请求失败，请检查本地服务。', response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  ask(question: string) {
    return request<AskResponse>('/ask', {
      method: 'POST',
      body: JSON.stringify({ question }),
    })
  },
  documents() {
    return request<DocumentListResponse>('/documents')
  },
  deleteDocument(id: string) {
    return request<void>(`/documents/${id}`, { method: 'DELETE' })
  },
  health() {
    return request<HealthResponse>('/health')
  },
  runEvaluation(cases: unknown[]) {
    return request<EvaluationRun>('/evaluations/run', {
      method: 'POST',
      body: JSON.stringify({ cases }),
    })
  },
  evaluationRuns() {
    return request<{ items: EvaluationRun[]; total: number }>('/evaluations/runs')
  },
}
