import { about } from '../data/content'

export function AboutSection() {
  return (
    <section id="about" className="section section-last">
      <h2 className="section-heading">{about.heading}</h2>
      <p className="primer">{about.body}</p>
    </section>
  )
}
