# Manual Collection Curation Guide

Use this guide to verify manually collected Bocconi web pages before converting them into markdown for the RAG dataset. Do not add a page because it is Bocconi-branded; add it only when it gives concrete, answerable information for one of the four required verticals.

## Existing Dataset Style

Production files under `backend/data/{vertical}/` are markdown files grouped by vertical. They use YAML front matter with at least:

```yaml
---
verticale: relocation
language: en
source_url: https://www.example.edu/page
last_updated: '2026-05-02'
title: Page Title
token_estimate: 1234
---
```

Manual curated files should follow the same spirit, but include verification metadata:

```yaml
---
title: Exact page title
source_url: https://www.unibocconi.it/example
fetched_at: '2026-05-09'
vertical: relocation
confidence: high
notes: "Why this page was accepted; mention stale or uncertain facts."
---
```

Use `vertical` in manual files because the staging requirement asks for it. If later merging into production, map it to the production field name `verticale`.

## Relevance Decision

Accept only pages that pass all baseline checks:

- The source URL is present and publicly attributable.
- The page contains factual content, not only navigation, slogans, generic positioning, news teasers, or image galleries.
- The content helps answer likely Bocconi student questions in one of the four verticals.
- The facts are grounded in the page text: requirements, dates, fees, contacts, locations, forms, offices, eligibility, procedures, or concrete program/service descriptions.
- The page is not a duplicate or near-duplicate of a better existing candidate.
- The page is not materially contradicted by a newer page in the same candidate batch.

Reject pages when any of these apply:

- Irrelevant to Bocconi students or the four verticals.
- Thin content: fewer than two useful factual points after removing navigation and marketing copy.
- Marketing-only: mostly claims such as "world-class", "unique", "transformative", "join our community" without operational facts.
- Duplicate: same source URL, same canonical URL, or substantially the same factual body as an accepted page.
- Unsafe or private: includes personal data that is not an official public office contact.
- Unusable source: missing URL, paywalled/inaccessible source text, corrupted extraction, or no reliable title/body.

## Vertical Rubric

### `relocation`

Accept if the page helps students move to or live in Milan while studying at Bocconi. Strong signals:

- Housing options, residence halls, booking procedures, eligibility, rates, deposits, room assignment, cancellation, renewal, sublease, guest/residence rules.
- Visa, permit of stay, fiscal code, bank account, health insurance/SSN, emergency numbers, airport transfer, public transport, neighborhood or cost-of-living information.
- Concrete locations, addresses, opening hours, official portals, application windows, required documents, fees, or deadlines.

Reject for `relocation`:

- Generic "why Milan" lifestyle promotion without actionable facts.
- City tourism pages not relevant to settling, transport, safety, housing, or student essentials.
- Housing articles without Bocconi/student relevance and without concrete rates, requirements, or process details.

### `life_on_campus`

Accept if the page helps students use campus services or participate in student life. Strong signals:

- Campus services: library, language center, IT support, dining, sport center, buildings/classrooms, badge services, student offices.
- Well-being, counseling, inclusion, disability/learning-disorder support, mental health resources, mindfulness, safety on campus.
- Student associations, volunteering, arts/culture, events, campus facilities, official student community resources.
- Concrete access rules, booking links, opening hours, locations, eligibility, contacts, forms, deadlines, or service procedures.

Reject for `life_on_campus`:

- One-off past events with no reusable service, deadline, or student procedure.
- Student newspaper/opinion pieces unless they contain stable practical information.
- Generic campus branding or image-led pages with no operational student facts.

### `study_abroad`

Accept if the page helps students participate in international academic mobility. Strong signals:

- Exchange, double degree, CEMS, free mover, summer school, incoming exchange, partner schools, international internships/scholarships.
- Selection criteria, eligibility, GPA/language requirements, exam registration cutoffs, application windows, rankings, academic recognition, transcripts, course load.
- Destination-specific warnings only when relevant to mobility decisions and clearly sourced from official public advisories.
- Concrete deadlines, requirements, portals, contacts, partner lists, fees/costs, insurance/visa steps for exchange students.

Reject for `study_abroad`:

- General international branding, rankings, or "global network" copy without application or mobility facts.
- Regular degree admissions pages unless they specifically cover international mobility or incoming exchange logistics.
- Travel content not tied to Bocconi mobility, academic recognition, safety advisories, or student requirements.

### `career_readiness`

Accept if the page helps students prepare for careers, internships, placement, employers, graduate outcomes, or professional development. Strong signals:

- Career Services, JobGate, internship activation/recognition, employer events, career fairs, CV/interview guidance, mentoring, alumni career support.
- Program placement pages, graduate employment statistics, sector/function/geography outcomes, internship requirements.
- Research centers/departments only when they help answer employability, recruiting, doctoral/research career, or program-career questions.
- Concrete figures, eligibility, deadlines, office contacts, portals, service descriptions, event/application requirements.

Reject for `career_readiness`:

- Faculty biographies, publications, research news, or executive education marketing unless directly useful for student career questions.
- Corporate partner logos/lists without context on recruiting access or student action.
- Program promotion without placement, internship, admissions-to-career, or professional outcome facts.

## Confidence Labels

- `high`: Official Bocconi/SDA/Bocconi Alumni/public authority source, clearly current or fetched date is known, and the extracted facts are explicit.
- `medium`: Source is relevant and factual, but some dates may be stale, the page is from a partner/third-party source, or the extraction is incomplete but still useful.
- `low`: Use only when the content is relevant but needs human review before indexing; label uncertain or stale facts in notes and body.

Do not convert pages with lower than `low` confidence. Reject instead.

## Markdown Conversion Rules

- Keep the `source_url`; never create a curated markdown file without it.
- Include `fetched_at` if known. If unknown, use `unknown` and explain in `notes`.
- Keep factual content only: requirements, deadlines, fees, contacts, addresses, opening hours, portals, procedures, eligibility, program/service descriptions, and concrete statistics.
- Remove marketing fluff, navigation crumbs, cookie banners, share links, repeated menus, image-only content, generic calls to action, and unsupported adjectives.
- Preserve concrete requirements, deadlines, contacts, fees, and statistics only when they are clearly present in the source text.
- Label stale or uncertain facts inline with `Note:` or in front matter `notes`; do not silently update or infer them.
- Do not include personal data unless it is an official public office contact, public service mailbox, official phone number, or public office address.
- Prefer concise sections and bullets over full-page dumps.
- Preserve original names of Bocconi services, portals, programs, scholarships, and offices.
- If the page mixes several verticals, assign the primary vertical and mention the cross-over in `notes`; do not duplicate unless distinct sections are independently valuable.
- Do not invent missing deadlines, fees, contacts, or titles. If a useful field is absent, omit it or mark it `unknown`.

## Later Workflow For `raw/pages.jsonl`

1. Read each candidate record from `backend/data/manual_collection/raw/pages.jsonl`.
2. Normalize URL and title for duplicate detection.
3. Score relevance against the vertical rubric.
4. Reject irrelevant, duplicate, thin, marketing-only, stale-without-value, or unsafe pages.
5. Convert accepted pages into `backend/data/manual_collection/curated/{vertical}/`.
6. Use the conversion template in `templates/conversion_template.md`.
7. Produce `backend/data/manual_collection/curation_report.md` with accepted/rejected counts and reasons.

## Checklist Before Accepting A Page

- Source URL is present.
- Fetched date is present or explicitly unknown.
- One primary vertical is selected from the four allowed names.
- At least two concrete student-useful facts remain after cleanup.
- Any deadline, fee, requirement, contact, or statistic is directly sourced from the page.
- Stale or uncertain facts are labeled.
- No private personal data is included.
- The page is not a duplicate of an already accepted page.
- The markdown body is concise and grounded.
