import { useCallback, useEffect, useRef, useState } from 'react'
import { AboutSection } from './components/AboutSection'
import { ConversationSection } from './components/ConversationSection'
import { FloatingChat } from './components/FloatingChat'
import { LeftRail } from './components/LeftRail'
import { TrendingSection } from './components/TrendingSection'
import { VerticaleSection } from './components/VerticaleSection'
import { menu, verticaleSections } from './data/content'
import type { SectionId } from './data/content'
import { applyTheme, getInitialTheme, persistTheme } from './theme'
import type { Theme } from './theme'

export default function App() {
  const [active, setActive] = useState<SectionId>('conversation')
  const [theme, setTheme] = useState<Theme>(() => getInitialTheme())
  const [chatOpen, setChatOpen] = useState(false)
  const observerRef = useRef<IntersectionObserver | null>(null)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  function changeTheme(next: Theme) {
    setTheme(next)
    persistTheme(next)
  }

  useEffect(() => {
    const ids = menu.map((item) => item.id)
    const elements = ids
      .map((id) => document.getElementById(id))
      .filter((element): element is HTMLElement => element !== null)

    if (elements.length === 0) {
      return
    }

    const ratios = new Map<string, number>()
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          ratios.set(entry.target.id, entry.intersectionRatio)
        }

        let bestId: string | null = null
        let bestRatio = 0
        for (const [id, ratio] of ratios) {
          if (ratio > bestRatio) {
            bestId = id
            bestRatio = ratio
          }
        }

        if (bestId && bestRatio > 0) {
          setActive(bestId as SectionId)
        }
      },
      {
        rootMargin: '-20% 0px -55% 0px',
        threshold: [0, 0.1, 0.25, 0.5, 0.75, 1],
      },
    )

    observerRef.current = observer
    for (const element of elements) {
      observer.observe(element)
    }

    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key !== 'Escape') {
        return
      }

      event.preventDefault()
      setChatOpen((isOpen) => !isOpen)
    }

    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const onJump = useCallback((id: SectionId) => {
    const element = document.getElementById(id)
    if (!element) {
      return
    }

    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setActive(id)
  }, [])

  const onPickQuestion = useCallback((question: string) => {
    const element = document.getElementById('conversation')
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }

    setActive('conversation')
    window.dispatchEvent(new CustomEvent<string>('buddy:ask', { detail: question }))
  }, [])

  return (
    <div className="app">
      <LeftRail
        active={active}
        onJump={onJump}
        theme={theme}
        onThemeChange={changeTheme}
      />

      <main className="content">
        <ConversationSection />
        <TrendingSection onPickQuestion={onPickQuestion} />

        {verticaleSections.map((section) => (
          <VerticaleSection
            key={section.id}
            section={section}
            onPickExample={onPickQuestion}
          />
        ))}

        <AboutSection />
      </main>

      <FloatingChat open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  )
}
