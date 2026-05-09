import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'

const BACKEND_URL = (
  import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000'
).replace(/\/$/, '')

type Verticale =
  | 'relocation'
  | 'life_on_campus'
  | 'study_abroad'
  | 'career_readiness'

type AskResponse = {
  answer: string
  sources: string[]
  verticale: Verticale
}

type Message = {
  id: number
  role: 'user' | 'assistant'
  text: string
  sources?: string[]
  verticale?: Verticale
}

const verticaleLabels: Record<Verticale, string> = {
  relocation: 'Life in Milan',
  life_on_campus: 'Campus life',
  study_abroad: 'Study abroad',
  career_readiness: 'Career',
}

const examples = [
  'What is the price of an annual ATM transit pass for students under 27 in Milan?',
  'Provide a structured table of dining areas available on the Bocconi campus.',
  'How is the MSc graduate Exchange Program selection score weighted?',
  'What is the maximum amount of the Bocconi Merit Award tuition waiver for MSc students?',
]

function App() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const latestAssistant = useMemo(
    () => [...messages].reverse().find((message) => message.role === 'assistant'),
    [messages],
  )

  async function sendQuestion(nextQuestion: string) {
    const trimmedQuestion = nextQuestion.trim()
    if (!trimmedQuestion || isLoading) {
      return
    }

    setQuestion('')
    setError('')
    setIsLoading(true)
    setMessages((current) => [
      ...current,
      {
        id: Date.now(),
        role: 'user',
        text: trimmedQuestion,
      },
    ])

    try {
      const response = await fetch(`${BACKEND_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: trimmedQuestion }),
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      const data = (await response.json()) as AskResponse
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: 'assistant',
          text: data.answer,
          sources: data.sources,
          verticale: data.verticale,
        },
      ])
    } catch (caughtError) {
      const message =
        caughtError instanceof Error
          ? caughtError.message
          : 'The buddy could not be reached.'
      setQuestion(trimmedQuestion)
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void sendQuestion(question)
  }

  return (
    <main className="app-shell">
      <section className="workspace" aria-label="Bocconi AI Buddy">
        <header className="topbar">
          <div>
            <p className="eyebrow">Bocconi AI Buddy</p>
            <h1>Ask about student life, fast.</h1>
          </div>
          <div className="status-pill">4 areas covered</div>
        </header>

        <div className="content-grid">
          <section className="chat-panel" aria-label="Conversation">
            <div className="messages">
              {messages.length === 0 ? (
                <div className="empty-state">
                  <p className="eyebrow">Start here</p>
                  <h2>Choose a question or type your own.</h2>
                  <div className="example-grid">
                    {examples.map((example) => (
                      <button
                        className="example-button"
                        key={example}
                        onClick={() => void sendQuestion(example)}
                        type="button"
                      >
                        {example}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <article className={`message ${message.role}`} key={message.id}>
                    <div className="message-meta">
                      <span>{message.role === 'user' ? 'You' : 'Buddy'}</span>
                      {message.verticale ? (
                        <span className={`verticale ${message.verticale}`}>
                          {verticaleLabels[message.verticale]}
                        </span>
                      ) : null}
                    </div>
                    <p>{message.text}</p>
                    {message.sources?.length ? (
                      <div className="mobile-sources">
                        {message.sources.map((source) => (
                          <span className="source-chip" key={source}>
                            {source}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </article>
                ))
              )}

              {isLoading ? (
                <article className="message assistant pending">
                  <div className="message-meta">
                    <span>Buddy</span>
                  </div>
                  <p>Reading the Bocconi sources...</p>
                </article>
              ) : null}
            </div>

            {error ? (
              <div className="error-box" role="alert">
                <span>{error}</span>
                <button onClick={() => void sendQuestion(question)} type="button">
                  Try again
                </button>
              </div>
            ) : null}

            <form className="composer" onSubmit={handleSubmit}>
              <label className="sr-only" htmlFor="question">
                Ask the Bocconi AI Buddy
              </label>
              <textarea
                id="question"
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about housing, campus life, study abroad, or career..."
                rows={3}
                value={question}
              />
              <button disabled={isLoading || !question.trim()} type="submit">
                Send
              </button>
            </form>
          </section>

          <aside className="context-panel" aria-label="Sources">
            <p className="eyebrow">Context</p>
            {latestAssistant?.verticale ? (
              <span className={`verticale ${latestAssistant.verticale}`}>
                {verticaleLabels[latestAssistant.verticale]}
              </span>
            ) : (
              <span className="muted">No question yet</span>
            )}

            <div className="source-list">
              {latestAssistant?.sources?.length ? (
                latestAssistant.sources.map((source) => (
                  <span className="source-chip" key={source}>
                    {source}
                  </span>
                ))
              ) : (
                <p className="muted">
                  Sources from the Bocconi dataset will appear after each answer.
                </p>
              )}
            </div>
          </aside>
        </div>
      </section>
    </main>
  )
}

export default App
