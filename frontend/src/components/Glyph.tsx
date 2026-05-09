import type { MenuItem } from '../data/content'

type Props = {
  name: MenuItem['glyph']
  size?: number
}

export function Glyph({ name, size = 16 }: Props) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  }

  switch (name) {
    case 'chat':
      return (
        <svg {...common}>
          <path d="M4 5h16v11H9l-5 4V5z" />
        </svg>
      )
    case 'relocation':
      return (
        <svg {...common}>
          <path d="M2 20h20" />
          <path d="M3 20v-6l3-2 2 2 1-1 2 2v-9l3 3 1-2 3 3 2-1v11" />
        </svg>
      )
    case 'life_on_campus':
      return (
        <svg {...common}>
          <path d="M4 20V10a8 8 0 0 1 16 0v10" />
          <path d="M4 20h16" />
          <path d="M9 20v-6a3 3 0 0 1 6 0v6" />
        </svg>
      )
    case 'study_abroad':
      return (
        <svg {...common}>
          <circle cx="11" cy="12" r="7" />
          <path d="M4 12h14" />
          <path d="M11 5c2.5 2 2.5 12 0 14" />
          <path d="M16 8l5-3-1 4" />
        </svg>
      )
    case 'career_readiness':
      return (
        <svg {...common}>
          <path d="M5 3h10l4 4v14H5z" />
          <path d="M15 3v4h4" />
          <path d="M8 12h8" />
          <path d="M8 16h8" />
        </svg>
      )
    case 'trending':
      return (
        <svg {...common}>
          <path d="M3 20h18" />
          <path d="M3 20V8" />
          <path d="M5 17l4-5 4 3 6-8" />
          <path d="M14 7h5v5" />
        </svg>
      )
    case 'about':
      return (
        <svg {...common} fill="currentColor">
          <rect x="6" y="6" width="12" height="12" />
        </svg>
      )
  }
}
