import type { VerticaleSectionContent } from '../data/content'

type Props = {
  section: VerticaleSectionContent
  onPickExample: (question: string) => void
}

export function VerticaleSection({ section, onPickExample }: Props) {
  return (
    <section id={section.id} className="section">
      <h2 className="section-heading">{section.heading}</h2>
      <p className="primer">{section.primer}</p>

      <h3 className="subheading mono">EXAMPLE QUESTIONS</h3>
      <ol className="example-list">
        {section.examples.map((question, index) => (
          <li key={question}>
            <button
              type="button"
              className="example-button"
              onClick={() => onPickExample(question)}
            >
              <span className="example-num mono">
                {String(index + 1).padStart(2, '0')}
              </span>
              <span className="example-text">{question}</span>
            </button>
          </li>
        ))}
      </ol>

      <h3 className="subheading mono">RESOURCES</h3>
      <ul className="resource-list">
        {section.resources.map((resource) => (
          <li key={resource.url}>
            <a
              className="resource-link"
              href={resource.url}
              target="_blank"
              rel="noreferrer noopener"
            >
              <span className="resource-label">{resource.label}</span>
              <span className="resource-arrow mono" aria-hidden>
                ^
              </span>
            </a>
            <span className="resource-host mono">{hostnameOf(resource.url)}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}
