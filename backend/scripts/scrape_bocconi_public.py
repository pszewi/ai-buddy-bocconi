#!/usr/bin/env python3
"""Polite first-pass collector for public Bocconi pages.

This script stages candidate RAG source pages only. It does not call OpenAI,
the app, or write into production vertical folders.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import time
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib import robotparser
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen


ROOT_URL = "https://www.unibocconi.it/en"
ALLOWED_HOST = "www.unibocconi.it"
USER_AGENT = "BocconiAIBuddyScraper/0.1 (candidate RAG collection; polite; no auth)"

VERTICAL_KEYWORDS = {
    "relocation": [
        "housing",
        "residence",
        "accommodation",
        "milan",
        "milano",
        "visa",
        "permit",
        "fiscal code",
        "health insurance",
        "arrival",
        "arrive",
        "international students",
        "freshly enrolled",
        "costs",
    ],
    "life_on_campus": [
        "campus life",
        "student activities",
        "associations",
        "library",
        "language center",
        "sport",
        "wellbeing",
        "counseling",
        "inclusion",
        "technology",
        "wifi",
        "current students",
    ],
    "study_abroad": [
        "international mobility",
        "exchange program",
        "exchange students",
        "double degree",
        "free mover",
        "study abroad",
        "partner schools",
        "incoming exchange",
        "academic recognition",
    ],
    "career_readiness": [
        "career services",
        "internship",
        "placement",
        "employers",
        "bocconijobs",
        "job market",
        "recruiting",
        "career opportunities",
        "professional opportunities",
        "meet employers",
    ],
}

SEED_PATHS = [
    "/en",
    "/en/current-students",
    "/en/current-students/housing",
    "/en/international-students",
    "/en/international-students/freshly-enrolled-students",
    "/en/current-students/campus-life",
    "/en/current-students/library-archives",
    "/en/current-students/language-center",
    "/en/current-students/international-mobility",
    "/en/international-students/incoming-exchange-students",
    "/en/current-students/career-services",
]

SKIP_EXTENSIONS = {
    ".7z",
    ".avi",
    ".css",
    ".csv",
    ".doc",
    ".docx",
    ".gif",
    ".ics",
    ".jpeg",
    ".jpg",
    ".js",
    ".mov",
    ".mp3",
    ".mp4",
    ".png",
    ".ppt",
    ".pptx",
    ".rar",
    ".svg",
    ".webp",
    ".xls",
    ".xlsx",
    ".zip",
}

BLOCKED_PATH_PARTS = (
    "/admin/",
    "/comment/reply/",
    "/filter/tips",
    "/media/oembed",
    "/node/add/",
    "/search/",
    "/user/",
    "/error/",
)


@dataclass
class FetchResult:
    url: str
    status: str
    content_type: str = ""
    body: bytes = b""
    note: str = ""


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self.lang = ""
        self._tag_stack: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        self._tag_stack.append(tag)
        if tag == "html":
            self.lang = attrs_dict.get("lang", "")
        if tag in {"script", "style", "noscript", "svg", "form", "nav", "footer"}:
            self._skip_depth += 1
        if tag == "a" and attrs_dict.get("href"):
            self.links.append(attrs_dict["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "form", "nav", "footer"} and self._skip_depth:
            self._skip_depth -= 1
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        text = clean_space(data)
        if not text:
            return
        if self._tag_stack and self._tag_stack[-1] == "title":
            self.title_parts.append(text)
        elif self._skip_depth == 0:
            self.text_parts.append(text)


def clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def normalize_url(raw_url: str, base_url: str) -> str | None:
    url, _fragment = urldefrag(urljoin(base_url, raw_url))
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc != ALLOWED_HOST:
        return None
    if not parsed.path.startswith("/en"):
        return None
    if parsed.query:
        return None
    lowered_path = parsed.path.lower()
    if any(part in lowered_path for part in BLOCKED_PATH_PARTS):
        return None
    if any(lowered_path.endswith(ext) for ext in SKIP_EXTENSIONS):
        return None
    return parsed._replace(scheme="https", fragment="", query="").geturl()


def infer_verticals(title: str, text: str, url: str) -> list[str]:
    haystack = f"{url} {title} {text[:5000]}".lower()
    scored: list[tuple[str, int]] = []
    for vertical, keywords in VERTICAL_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score:
            scored.append((vertical, score))
    return [vertical for vertical, _score in sorted(scored, key=lambda item: (-item[1], item[0]))]


def relevance_score(url: str, title: str = "", text: str = "") -> int:
    haystack = f"{url} {title} {text[:3000]}".lower()
    score = sum(len(VERTICAL_KEYWORDS[v]) - i for v in VERTICAL_KEYWORDS for i, kw in enumerate(VERTICAL_KEYWORDS[v]) if kw in haystack)
    path = urlparse(url).path.lower()
    if any(
        part in path
        for part in (
            "/current-students/",
            "/international-students/",
            "/career-services",
            "/international-mobility",
            "/incoming-exchange-students",
            "/housing",
            "/campus-life",
        )
    ):
        score += 25
    if "/news/" in path or "/faculty-and-research/" in path or "/hub-news-and-events" in path:
        score -= 30
    return score


def fetch_url(url: str, timeout: int) -> FetchResult:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read(2_000_000)
            return FetchResult(url=url, status=f"HTTP {response.status}", content_type=content_type, body=body)
    except HTTPError as exc:
        return FetchResult(url=url, status=f"HTTP {exc.code}", note=str(exc.reason))
    except URLError as exc:
        return FetchResult(url=url, status="URL_ERROR", note=str(exc.reason))
    except TimeoutError:
        return FetchResult(url=url, status="TIMEOUT")


def parse_html(body: bytes) -> PageParser:
    parser = PageParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    return parser


def load_robot_parser() -> robotparser.RobotFileParser:
    parser = robotparser.RobotFileParser()
    parser.set_url(f"https://{ALLOWED_HOST}/robots.txt")
    parser.read()
    return parser


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def crawl(max_pages: int, max_depth: int, delay: float, timeout: int, output_dir: Path) -> tuple[list[dict], list[dict], Counter[str]]:
    robots = load_robot_parser()
    fetched: list[dict] = []
    skipped: list[dict] = []
    status_counts: Counter[str] = Counter()
    seen: set[str] = set()
    queue = deque((f"https://{ALLOWED_HOST}{path}", 0) for path in SEED_PATHS)

    while queue and len(fetched) < max_pages:
        url, depth = queue.popleft()
        normalized = normalize_url(url, ROOT_URL)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)

        if not robots.can_fetch(USER_AGENT, normalized):
            skipped.append({"url": normalized, "reason": "robots_disallow"})
            continue

        result = fetch_url(normalized, timeout)
        status_counts[result.status] += 1
        fetched_at = datetime.now(timezone.utc).isoformat()

        if result.status != "HTTP 200":
            skipped.append({"url": normalized, "reason": result.status, "notes": result.note})
            time.sleep(delay)
            continue
        if "text/html" not in result.content_type.lower():
            skipped.append({"url": normalized, "reason": "non_html", "content_type": result.content_type})
            time.sleep(delay)
            continue

        parser = parse_html(result.body)
        title = clean_space(" ".join(parser.title_parts))
        cleaned_text = clean_space(" ".join(parser.text_parts))
        vertical_hints = infer_verticals(title, cleaned_text, normalized)
        if not vertical_hints:
            skipped.append({"url": normalized, "reason": "low_relevance", "title": title})
        else:
            fetched.append(
                {
                    "url": normalized,
                    "fetched_at": fetched_at,
                    "title": title,
                    "language": parser.lang or "en",
                    "vertical_hints": vertical_hints,
                    "cleaned_text": cleaned_text[:12_000],
                    "text_excerpt": cleaned_text[:700],
                    "source_status": result.status,
                    "notes": f"content_type={result.content_type}; crawl_depth={depth}",
                }
            )

        if depth < max_depth:
            candidates = []
            for link in parser.links:
                next_url = normalize_url(link, normalized)
                if next_url and next_url not in seen:
                    candidates.append(next_url)
            for next_url in sorted(set(candidates), key=lambda item: -relevance_score(item)):
                queue.append((next_url, depth + 1))

        time.sleep(delay)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "pages.jsonl", fetched)
    write_jsonl(output_dir / "skipped_urls.jsonl", skipped)
    return fetched, skipped, status_counts


def render_manifest(fetched: list[dict], skipped: list[dict], status_counts: Counter[str], args: argparse.Namespace) -> str:
    vertical_counts = Counter(vertical for row in fetched for vertical in row["vertical_hints"])
    promising = sorted(
        fetched,
        key=lambda row: (-relevance_score(row["url"], row["title"], row["cleaned_text"]), row["url"]),
    )[:10]
    skipped_counts = Counter(row["reason"] for row in skipped)
    lines = [
        "# Bocconi Public Web Candidate Crawl",
        "",
        f"- Start URL: `{ROOT_URL}`",
        f"- Fetched at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- User agent: `{USER_AGENT}`",
        f"- Max candidate pages: `{args.max_pages}`",
        f"- Max crawl depth: `{args.max_depth}`",
        f"- Delay between requests: `{args.delay_seconds}` seconds",
        f"- Timeout: `{args.timeout}` seconds",
        "- Scope: public `https://www.unibocconi.it/en` HTML pages only; skipped queries, files, forms, auth/search/admin/oembed/error paths, and non-English paths.",
        "- Robots: checked `https://www.unibocconi.it/robots.txt` with `urllib.robotparser`; disallowed URLs were not fetched.",
        "",
        "## Counts",
        "",
        f"- Candidate pages written: `{len(fetched)}`",
        f"- Skipped URLs recorded: `{len(skipped)}`",
        f"- HTTP/status counts: `{dict(status_counts)}`",
        f"- Vertical hint counts: `{dict(vertical_counts)}`",
        f"- Skipped reason counts: `{dict(skipped_counts)}`",
        "",
        "## Relevance Observations",
        "",
        "- Strongest public areas for this pass were Career Services, International Mobility, Incoming Exchange Students, Housing, and Campus Life.",
        "- Some pages are broad navigation or listing pages; candidates should be reviewed before merging into production RAG data.",
        "- `cleaned_text` is truncated to 12,000 characters per page for staging review, not final chunking.",
        "",
        "## Top Promising URLs",
        "",
    ]
    for row in promising:
        lines.append(f"- {row['url']} ({', '.join(row['vertical_hints'])})")
    lines.extend(["", "## Skipped URL Log", "", "- Full skipped URL records are in `skipped_urls.jsonl`."])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=60)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--delay-seconds", type=float, default=0.75)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=Path("backend/data/manual_collection/raw"))
    args = parser.parse_args()

    fetched, skipped, status_counts = crawl(
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        delay=args.delay_seconds,
        timeout=args.timeout,
        output_dir=args.output_dir,
    )
    (args.output_dir / "manifest.md").write_text(render_manifest(fetched, skipped, status_counts, args), encoding="utf-8")
    print(f"candidate_pages={len(fetched)} skipped={len(skipped)} output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
