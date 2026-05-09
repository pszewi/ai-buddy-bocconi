import type {
  AskResponse,
  ChatTurn,
  RecentQuestion,
  Verticale,
} from './data/content'

const BACKEND_URL = (
  import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000'
).replace(/\/$/, '')

const VERTICALES = new Set<Verticale>([
  'relocation',
  'life_on_campus',
  'study_abroad',
  'career_readiness',
])

export async function askBuddy(
  question: string,
  history: ChatTurn[] = [],
): Promise<AskResponse> {
  const response = await fetch(`${BACKEND_URL}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question, history }),
  })

  if (!response.ok) {
    throw new Error(`The buddy returned HTTP ${response.status}.`)
  }

  const data: unknown = await response.json()
  if (!isAskResponse(data)) {
    throw new Error('The buddy returned an unexpected response shape.')
  }

  return data
}

export async function getRecentQuestions(): Promise<RecentQuestion[]> {
  const response = await fetch(`${BACKEND_URL}/recent-questions`)

  if (!response.ok) {
    throw new Error(`The buddy returned HTTP ${response.status}.`)
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data)) {
    throw new Error('The buddy returned an unexpected recent-question shape.')
  }

  return data.filter(isRecentQuestion)
}

function isAskResponse(data: unknown): data is AskResponse {
  if (!data || typeof data !== 'object') {
    return false
  }

  const candidate = data as Record<string, unknown>
  return (
    typeof candidate.answer === 'string' &&
    Array.isArray(candidate.sources) &&
    candidate.sources.every((source) => typeof source === 'string') &&
    typeof candidate.verticale === 'string' &&
    VERTICALES.has(candidate.verticale as Verticale)
  )
}

function isRecentQuestion(data: unknown): data is RecentQuestion {
  if (!data || typeof data !== 'object') {
    return false
  }

  const candidate = data as Record<string, unknown>
  return (
    typeof candidate.question === 'string' &&
    typeof candidate.count === 'number' &&
    typeof candidate.asked_at === 'number' &&
    typeof candidate.verticale === 'string' &&
    VERTICALES.has(candidate.verticale as Verticale)
  )
}

export function friendlyError(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message
  }

  return 'The buddy could not be reached. Check that the backend is running.'
}
