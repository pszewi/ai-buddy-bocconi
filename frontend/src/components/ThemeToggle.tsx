import type { Theme } from '../theme'

type Props = {
  theme: Theme
  onChange: (next: Theme) => void
}

export function ThemeToggle({ theme, onChange }: Props) {
  return (
    <div className="theme-toggle" aria-label="Theme">
      <button
        type="button"
        className={`theme-toggle-button${theme === 'light' ? ' is-active' : ''}`}
        onClick={() => onChange('light')}
        aria-pressed={theme === 'light'}
      >
        light
      </button>
      <span className="theme-toggle-sep" aria-hidden>
        /
      </span>
      <button
        type="button"
        className={`theme-toggle-button${theme === 'dark' ? ' is-active' : ''}`}
        onClick={() => onChange('dark')}
        aria-pressed={theme === 'dark'}
      >
        dark
      </button>
    </div>
  )
}
