import { useCallback, useEffect, useRef, useState } from 'react'
import { askBuddy, friendlyError } from '../api'
import { verticaleLabel } from '../data/content'
import type { AskResponse, ChatTurn } from '../data/content'
import { MarkdownAnswer } from './MarkdownAnswer'

type Exchange = {
  id: number
  question: string
  askedAt: number
  status: 'pending' | 'answered' | 'error'
  response?: AskResponse
  error?: string
}

const RECENT_CAP = 3

function historyFromExchanges(exchanges: Exchange[]): ChatTurn[] {
  return exchanges
    .slice()
    .reverse()
    .flatMap((exchange) => {
      const turns: ChatTurn[] = [{ role: 'user', content: exchange.question }]
      if (exchange.status === 'answered' && exchange.response) {
        turns.push({ role: 'assistant', content: exchange.response.answer })
      }
      return turns
    })
    .slice(-8)
}

function formatRelative(askedAt: number, now: number): string {
  const diffSec = Math.max(1, Math.floor((now - askedAt) / 1000))
  if (diffSec < 60) {
    return `${diffSec}s ago`
  }

  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) {
    return `${diffMin} min ago`
  }

  const diffHour = Math.floor(diffMin / 60)
  return `${diffHour}h ago`
}

export function ConversationSection() {
  const [exchanges, setExchanges] = useState<Exchange[]>([])
  const [draft, setDraft] = useState('')
  const [now, setNow] = useState(() => Date.now())
  const idRef = useRef(0)
  const loadingRef = useRef(false)
  const exchangesRef = useRef<Exchange[]>([])
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const isLoading = exchanges.some((exchange) => exchange.status === 'pending')
  const recent = exchanges.slice(0, RECENT_CAP)

  useEffect(() => {
    exchangesRef.current = exchanges
  }, [exchanges])

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 30_000)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key !== '/') {
        return
      }

      const target = event.target as HTMLElement | null
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable)
      ) {
        return
      }

      event.preventDefault()
      textareaRef.current?.focus()
    }

    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const submit = useCallback(async (question: string) => {
    const trimmed = question.trim()
    if (!trimmed || loadingRef.current) {
      return
    }

    loadingRef.current = true
    const id = idRef.current++
    setDraft('')
    setExchanges((current) => [
      {
        id,
        askedAt: Date.now(),
        question: trimmed,
        status: 'pending',
      },
      ...current,
    ])

    const history = historyFromExchanges(exchangesRef.current)

    try {
      const response = await askBuddy(trimmed, history)
      setExchanges((current) =>
        current.map((exchange) =>
          exchange.id === id
            ? { ...exchange, response, status: 'answered' }
            : exchange,
        ),
      )
    } catch (error) {
      setDraft(trimmed)
      setExchanges((current) =>
        current.map((exchange) =>
          exchange.id === id
            ? { ...exchange, error: friendlyError(error), status: 'error' }
            : exchange,
        ),
      )
    } finally {
      loadingRef.current = false
    }
  }, [])

  useEffect(() => {
    function onAsk(event: Event) {
      const detail = (event as CustomEvent<string>).detail
      if (!detail) {
        return
      }

      void submit(detail)
    }

    window.addEventListener('buddy:ask', onAsk)
    return () => window.removeEventListener('buddy:ask', onAsk)
  }, [submit])

  function send() {
    void submit(draft)
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      send()
    }
  }

  return (
    <section id="conversation" className="section">
      <h2 className="section-heading">ask</h2>
      <p className="primer conversation-primer">
        Ask in English or Italian. Follow-ups include the recent local thread,
        and grounded answers show the backend sources used.
      </p>

      <div className="composer">
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder="ask anything..."
          rows={3}
          aria-label="Ask a question"
        />
        <button
          type="button"
          className="composer-send"
          onClick={send}
          disabled={!draft.trim() || isLoading}
        >
          send -&gt;
        </button>
      </div>

      <div className="composer-hints mono">
        <span>press</span> <kbd>/</kbd> <span>to focus</span>{' '}
        <span className="dot">/</span> <kbd>Enter</kbd> <span>to send</span>{' '}
        <span className="dot">/</span> <kbd>Shift</kbd>+<kbd>Enter</kbd>{' '}
        <span>for newline</span>
      </div>
      <div className="escape-hint">
        want to keep talking? press <kbd>esc</kbd> to open a floating
        conversation.
      </div>

      {exchanges.length === 0 ? (
        <p className="status-note">
          Start with a question here, choose an example below, or try a trending
          prompt. Each turn calls <span className="mono">POST /ask</span> with
          the latest question plus the local thread history.
        </p>
      ) : (
        <div className="conversation-thread">
          {exchanges.map((exchange) => (
            <article className="featured" key={exchange.id}>
              <div className="qa-q">
                <span className="qa-mark mono">Q</span>
                <p>{exchange.question}</p>
              </div>

              {exchange.status === 'pending' ? (
                <div className="qa-a pending">
                  <div className="msg-eyebrow mono">
                    BUDDY / SOURCES / thinking
                    <span className="caret" />
                  </div>
                </div>
              ) : null}

              {exchange.status === 'error' ? (
                <div className="qa-a error" role="alert">
                  <div className="msg-eyebrow mono">BUDDY / ERROR</div>
                  <p className="msg-body">
                    {exchange.error ?? 'The buddy could not be reached.'}
                  </p>
                  <button
                    type="button"
                    className="retry-button"
                    onClick={() => void submit(exchange.question)}
                    disabled={isLoading}
                  >
                    try again
                  </button>
                </div>
              ) : null}

              {exchange.status === 'answered' && exchange.response ? (
                <div className="qa-a">
                  <div className="msg-eyebrow mono">
                    BUDDY / {verticaleLabel[exchange.response.verticale]}
                  </div>
                  <MarkdownAnswer
                    className="msg-body"
                    text={exchange.response.answer}
                  />
                  <hr className="rule" />
                  {exchange.response.sources.length > 0 ? (
                    <ol className="sources mono">
                      {exchange.response.sources.map((source, index) => (
                        <li key={source}>
                          <span className="source-num">[{index + 1}]</span>
                          {source}
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="sources-empty mono">No sources returned.</p>
                  )}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      )}

      {recent.length > 0 && (
        <section className="recent">
          <h3 className="recent-heading mono">RECENTLY ASKED</h3>
          <ol className="recent-list">
            {recent.map((entry) => (
              <li key={`${entry.askedAt}-${entry.question}`}>
                <button
                  type="button"
                  className="recent-button"
                  onClick={() => void submit(entry.question)}
                  disabled={isLoading}
                >
                  <span className="recent-time mono">
                    {formatRelative(entry.askedAt, now)}
                  </span>
                  <span className="recent-q">{entry.question}</span>
                </button>
              </li>
            ))}
          </ol>
        </section>
      )}
    </section>
  )
}
