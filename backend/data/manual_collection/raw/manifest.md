# Bocconi Public Web Candidate Crawl

- Start URL: `https://www.unibocconi.it/en`
- Fetched at: `2026-05-09T12:59:39.145566+00:00`
- User agent: `BocconiAIBuddyScraper/0.1 (candidate RAG collection; polite; no auth)`
- Max candidate pages: `60`
- Max crawl depth: `3`
- Delay between requests: `0.75` seconds
- Timeout: `20` seconds
- Scope: public `https://www.unibocconi.it/en` HTML pages only; skipped queries, files, forms, auth/search/admin/oembed/error paths, and non-English paths.
- Robots: checked `https://www.unibocconi.it/robots.txt` with `urllib.robotparser`; disallowed URLs were not fetched.

## Counts

- Candidate pages written: `60`
- Skipped URLs recorded: `13`
- HTTP/status counts: `{'HTTP 200': 72, 'HTTP 404': 1}`
- Vertical hint counts: `{'life_on_campus': 49, 'relocation': 30, 'career_readiness': 18, 'study_abroad': 15}`
- Skipped reason counts: `{'low_relevance': 12, 'HTTP 404': 1}`

## Relevance Observations

- Strongest public areas for this pass were Career Services, International Mobility, Incoming Exchange Students, Housing, and Campus Life.
- Some pages are broad navigation or listing pages; candidates should be reviewed before merging into production RAG data.
- `cleaned_text` is truncated to 12,000 characters per page for staging review, not final chunking.

## Top Promising URLs

- https://www.unibocconi.it/en/international-students/incoming-exchange-students (relocation, life_on_campus, study_abroad, career_readiness)
- https://www.unibocconi.it/en/international-students/freshly-enrolled-students-when-you-arrive (relocation, life_on_campus, study_abroad)
- https://www.unibocconi.it/en/current-students/housing (relocation, study_abroad, career_readiness, life_on_campus)
- https://www.unibocconi.it/en/current-students (life_on_campus, relocation, career_readiness)
- https://www.unibocconi.it/en/current-students/campus-life (life_on_campus)
- https://www.unibocconi.it/en/international-students/freshly-enrolled-students-you-arrive (relocation)
- https://www.unibocconi.it/en/current-students/career-services (career_readiness, life_on_campus)
- https://www.unibocconi.it/en/applying-bocconi/master-science-and-ma-programs (relocation, career_readiness, study_abroad)
- https://www.unibocconi.it/en/international-students/current-students (life_on_campus, relocation, career_readiness)
- https://www.unibocconi.it/en/current-students/international-mobility (study_abroad, life_on_campus)

## Skipped URL Log

- Full skipped URL records are in `skipped_urls.jsonl`.
