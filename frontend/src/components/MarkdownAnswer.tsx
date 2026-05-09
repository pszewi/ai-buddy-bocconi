import type { ReactNode } from 'react'

type Props = {
  text: string
  className?: string
}

type Block =
  | { type: 'paragraph'; text: string }
  | { type: 'heading'; level: 3 | 4; text: string }
  | { type: 'ul' | 'ol'; items: string[] }

const INLINE_PATTERN = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\((?:https?:\/\/|mailto:)[^)]+\))/g

function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = []
  let lastIndex = 0

  for (const match of text.matchAll(INLINE_PATTERN)) {
    const [token] = match
    const index = match.index ?? 0

    if (index > lastIndex) {
      nodes.push(text.slice(lastIndex, index))
    }

    if (token.startsWith('**') && token.endsWith('**')) {
      nodes.push(<strong key={`${index}-strong`}>{token.slice(2, -2)}</strong>)
    } else if (token.startsWith('`') && token.endsWith('`')) {
      nodes.push(<code key={`${index}-code`}>{token.slice(1, -1)}</code>)
    } else {
      const link = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
      if (link) {
        nodes.push(
          <a
            key={`${index}-link`}
            href={link[2]}
            target="_blank"
            rel="noreferrer"
          >
            {link[1]}
          </a>,
        )
      } else {
        nodes.push(token)
      }
    }

    lastIndex = index + token.length
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex))
  }

  return nodes
}

function parseBlocks(text: string): Block[] {
  const blocks: Block[] = []
  const lines = text.replace(/\r\n/g, '\n').split('\n')
  let paragraph: string[] = []

  function flushParagraph() {
    if (paragraph.length === 0) {
      return
    }

    blocks.push({ type: 'paragraph', text: paragraph.join(' ') })
    paragraph = []
  }

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim()

    if (!line) {
      flushParagraph()
      continue
    }

    const heading = line.match(/^#{1,4}\s+(.+)$/)
    if (heading) {
      flushParagraph()
      blocks.push({ type: 'heading', level: 3, text: heading[1] })
      continue
    }

    const unordered = line.match(/^[-*]\s+(.+)$/)
    if (unordered) {
      flushParagraph()
      const items = [unordered[1]]
      while (index + 1 < lines.length) {
        const next = lines[index + 1].trim().match(/^[-*]\s+(.+)$/)
        if (!next) {
          break
        }
        items.push(next[1])
        index += 1
      }
      blocks.push({ type: 'ul', items })
      continue
    }

    const ordered = line.match(/^\d+[.)]\s+(.+)$/)
    if (ordered) {
      flushParagraph()
      const items = [ordered[1]]
      while (index + 1 < lines.length) {
        const next = lines[index + 1].trim().match(/^\d+[.)]\s+(.+)$/)
        if (!next) {
          break
        }
        items.push(next[1])
        index += 1
      }
      blocks.push({ type: 'ol', items })
      continue
    }

    paragraph.push(line)
  }

  flushParagraph()
  return blocks
}

export function MarkdownAnswer({ text, className }: Props) {
  const blocks = parseBlocks(text)

  return (
    <div className={className ? `markdown-answer ${className}` : 'markdown-answer'}>
      {blocks.map((block, index) => {
        switch (block.type) {
          case 'heading':
            return <h3 key={index}>{renderInline(block.text)}</h3>
          case 'ul':
            return (
              <ul key={index}>
                {block.items.map((item, itemIndex) => (
                  <li key={itemIndex}>{renderInline(item)}</li>
                ))}
              </ul>
            )
          case 'ol':
            return (
              <ol key={index}>
                {block.items.map((item, itemIndex) => (
                  <li key={itemIndex}>{renderInline(item)}</li>
                ))}
              </ol>
            )
          case 'paragraph':
            return <p key={index}>{renderInline(block.text)}</p>
        }
      })}
    </div>
  )
}
