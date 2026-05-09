import { useCallback, useEffect, useRef, useState } from 'react'
import { askBuddy, friendlyError } from '../api'
import { verticaleLabel } from '../data/content'
import type { AskResponse, ChatTurn } from '../data/content'
import { MarkdownAnswer } from './MarkdownAnswer'

type UserMsg = {
  id: number
  role: 'user'
  question: string
}

type AssistantMsg = {
  id: number
  role: 'assistant'
  response: AskResponse
}

type PendingMsg = {
  id: number
  role: 'pending'
}

type ErrorMsg = {
  id: number
  role: 'error'
  error: string
  question: string
}

type Msg = UserMsg | AssistantMsg | PendingMsg | ErrorMsg

type Props = {
  open: boolean
  onClose: () => void
}

function historyFromMessages(messages: Msg[]): ChatTurn[] {
  return messages
    .flatMap((message): ChatTurn[] => {
      if (message.role === 'user') {
        return [{ role: 'user', content: message.question }]
      }

      if (message.role === 'assistant') {
        return [{ role: 'assistant', content: message.response.answer }]
      }

      return []
    })
    .slice(-8)
}

export function FloatingChat({ open, onClose }: Props) {
  const [messages, setMessages] = useState<Msg[]>([])
  const [draft, setDraft] = useState('')
  const idRef = useRef(0)
  const loadingRef = useRef(false)
  const messagesRef = useRef<Msg[]>([])
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const threadRef = useRef<HTMLDivElement | null>(null)
  const isLoading = messages.some((message) => message.role === 'pending')

  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  useEffect(() => {
    if (!open) {
      return
    }

    const timer = window.setTimeout(() => textareaRef.current?.focus(), 30)
    return () => window.clearTimeout(timer)
  }, [open])

  useEffect(() => {
    if (!open || !threadRef.current) {
      return
    }

    threadRef.current.scrollTop = threadRef.current.scrollHeight
  }, [messages, open])

  const submit = useCallback(async (question: string) => {
    const trimmed = question.trim()
    if (!trimmed || loadingRef.current) {
      return
    }

    loadingRef.current = true
    const userId = idRef.current++
    const pendingId = idRef.current++
    setMessages((current) => [
      ...current,
      { id: userId, role: 'user', question: trimmed },
      { id: pendingId, role: 'pending' },
    ])
    setDraft('')

    const history = historyFromMessages(messagesRef.current)

    try {
      const response = await askBuddy(trimmed, history)
      setMessages((current) => [
        ...current.filter((message) => message.id !== pendingId),
        { id: idRef.current++, role: 'assistant', response },
      ])
    } catch (error) {
      setDraft(trimmed)
      setMessages((current) => [
        ...current.filter((message) => message.id !== pendingId),
        {
          id: idRef.current++,
          role: 'error',
          error: friendlyError(error),
          question: trimmed,
        },
      ])
    } finally {
      loadingRef.current = false
    }
  }, [])

  function send() {
    void submit(draft)
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      send()
    }

    if (event.key === 'Escape') {
      event.preventDefault()
      event.stopPropagation()
      onClose()
    }
  }

  if (!open) {
    return null
  }

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Floating conversation"
      onClick={onClose}
    >
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <header className="modal-header">
          <span className="modal-header-title">conversation</span>
          <span>
            <kbd>esc</kbd> to close
          </span>
        </header>

        <div className="modal-thread" ref={threadRef}>
          {messages.length === 0 ? (
            <p className="modal-thread-empty">
              Keep a local thread here. Each message calls /ask with your latest
              question plus recent local context.
            </p>
          ) : (
            messages.map((message) => {
              if (message.role === 'user') {
                return (
                  <div key={message.id} className="modal-msg is-user">
                    <div className="modal-msg-bubble">{message.question}</div>
                  </div>
                )
              }

              if (message.role === 'pending') {
                return (
                  <div key={message.id} className="modal-msg is-assistant">
                    <span className="modal-msg-eyebrow">
                      BUDDY / SOURCES / thinking
                      <span className="caret" />
                    </span>
                  </div>
                )
              }

              if (message.role === 'error') {
                return (
                  <div key={message.id} className="modal-msg is-assistant">
                    <span className="modal-msg-eyebrow">BUDDY / ERROR</span>
                    <div className="modal-msg-bubble">{message.error}</div>
                    <button
                      type="button"
                      className="modal-retry"
                      onClick={() => void submit(message.question)}
                      disabled={isLoading}
                    >
                      try again
                    </button>
                  </div>
                )
              }

              return (
                <div key={message.id} className="modal-msg is-assistant">
                  <span className="modal-msg-eyebrow">
                    BUDDY / {verticaleLabel[message.response.verticale]}
                  </span>
                  <MarkdownAnswer
                    className="modal-msg-bubble"
                    text={message.response.answer}
                  />
                  {message.response.sources.length > 0 ? (
                    <ol className="modal-sources">
                      {message.response.sources.map((source, index) => (
                        <li key={source}>
                          [{index + 1}] {source}
                        </li>
                      ))}
                    </ol>
                  ) : null}
                </div>
              )
            })
          )}
        </div>

        <div className="modal-composer">
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder="continue the conversation..."
            rows={1}
            aria-label="Continue the conversation"
          />
          <button
            type="button"
            className="modal-composer-send"
            onClick={send}
            disabled={!draft.trim() || isLoading}
          >
            send -&gt;
          </button>
        </div>

        <footer className="modal-footer">
          <span>
            <kbd>Enter</kbd> send / <kbd>Shift</kbd>+<kbd>Enter</kbd> newline
          </span>
          <span>local thread / /ask</span>
        </footer>
      </div>
    </div>
  )
}
