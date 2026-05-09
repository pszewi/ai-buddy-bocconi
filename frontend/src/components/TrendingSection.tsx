import { useEffect, useState } from 'react'
import { getRecentQuestions } from '../api'
import { trending } from '../data/content'
import { verticaleLabel } from '../data/content'
import type { RecentQuestion } from '../data/content'

type Props = {
  onPickQuestion: (question: string) => void
}

export function TrendingSection({ onPickQuestion }: Props) {
  const [recent, setRecent] = useState<RecentQuestion[]>([])
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let alive = true

    getRecentQuestions()
      .then((rows) => {
        if (alive) {
          setRecent(rows)
          setFailed(false)
        }
      })
      .catch(() => {
        if (alive) {
          setFailed(true)
        }
      })

    return () => {
      alive = false
    }
  }, [])

  const rows =
    recent.length > 0
      ? recent.map((row) => ({
          count: row.count,
          question: row.question,
          meta: verticaleLabel[row.verticale],
        }))
      : trending.map((row) => ({ ...row, meta: 'curated' }))

  return (
    <section id="trending" className="section">
      <h2 className="section-heading">trending</h2>
      <p className="primer">
        {recent.length > 0
          ? 'Recently submitted questions from this backend. Click one to ask Buddy again with the current retrieval stack.'
          : 'Curated prompts appear until the backend has recent submitted questions.'}
        {failed ? ' Live recent questions could not be loaded.' : ''}
      </p>
      <ol className="trending-list">
        {rows.map((row) => (
          <li key={row.question}>
            <button
              type="button"
              className="trending-button"
              onClick={() => onPickQuestion(row.question)}
            >
              <span className="trending-count mono">{row.count}x</span>
              <span className="trending-q">{row.question}</span>
              <span className="trending-meta mono">{row.meta}</span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  )
}
