import { menu } from '../data/content'
import type { SectionId } from '../data/content'
import type { Theme } from '../theme'
import { Glyph } from './Glyph'
import { ThemeToggle } from './ThemeToggle'

type Props = {
  active: SectionId
  onJump: (id: SectionId) => void
  theme: Theme
  onThemeChange: (next: Theme) => void
}

export function LeftRail({ active, onJump, theme, onThemeChange }: Props) {
  return (
    <aside className="left-rail">
      <div className="wordmark">
        <span>BOCCONI</span>
        <span>AI BUDDY</span>
      </div>

      <nav className="menu" aria-label="Sections">
        {menu.map((item) => {
          const isActive = item.id === active
          return (
            <button
              key={item.id}
              type="button"
              className={`menu-item${isActive ? ' is-active' : ''}`}
              onClick={() => onJump(item.id)}
              aria-current={isActive ? 'true' : undefined}
            >
              <span className="menu-bar" aria-hidden />
              <span className="menu-glyph">
                <Glyph name={item.glyph} />
              </span>
              <span className="menu-label">{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="rail-footer">
        <ThemeToggle theme={theme} onChange={onThemeChange} />
        <span className="mono">v0.2 / eu / 2026-05-09</span>
      </div>
    </aside>
  )
}
