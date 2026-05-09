"""Bocconi AI Buddy - backend entry point."""

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

app = FastAPI(title="Bocconi AI Buddy")

# CORS: allow the deployed frontend (and localhost during dev) to call /ask.
# Set FRONTEND_URL on Railway to your frontend service's public URL,
# e.g. https://buddy-frontend-yourname.up.railway.app
_allowed = [
    o.strip()
    for o in (os.environ.get("FRONTEND_URL") or "*").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


Verticale = Literal[
    "relocation",
    "life_on_campus",
    "study_abroad",
    "career_readiness",
]

VERTICALS: tuple[Verticale, ...] = (
    "relocation",
    "life_on_campus",
    "study_abroad",
    "career_readiness",
)

DATA_DIR = Path(os.environ.get("BUDDY_DATA_DIR", Path(__file__).with_name("data")))
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_'-]{1,}", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")

STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "can",
    "come",
    "con",
    "dei",
    "del",
    "della",
    "devo",
    "does",
    "for",
    "from",
    "gli",
    "has",
    "have",
    "how",
    "into",
    "its",
    "nel",
    "per",
    "qual",
    "quale",
    "sono",
    "the",
    "this",
    "una",
    "what",
    "when",
    "where",
    "which",
    "with",
    "you",
}

QUERY_SYNONYMS = {
    "adult": ["adulti", "adulto"],
    "adults": ["adulti", "adulto"],
    "annual": ["annuale", "annuali", "anno"],
    "answer": ["risposta"],
    "campus": ["campus"],
    "cost": ["costo", "costa", "prezzo"],
    "costs": ["costi", "prezzi"],
    "deadline": ["scadenza", "scadenze"],
    "dining": ["mensa", "ristorazione"],
    "health": ["salute", "sanitario", "sanitaria"],
    "library": ["biblioteca"],
    "milan": ["milano"],
    "monthly": ["mensile", "mese"],
    "pass": ["abbonamento", "abbonamenti", "tessera"],
    "passes": ["abbonamento", "abbonamenti", "tessere"],
    "price": ["prezzo", "costo", "costa", "pagano"],
    "prices": ["prezzi", "costi"],
    "service": ["servizio"],
    "standard": ["normale", "standard"],
    "student": ["studente", "studenti", "giovane", "giovani"],
    "students": ["studente", "studenti", "giovane", "giovani"],
    "transit": ["transport", "trasporto", "trasporti"],
    "transport": ["transit", "trasporto", "trasporti"],
    "under": ["sotto"],
    "urban": ["urbano", "urbana", "urbane"],
}

VERTICAL_KEYWORDS: dict[Verticale, dict[str, int]] = {
    "relocation": {
        "airport": 5,
        "atm": 5,
        "bank": 4,
        "bus": 3,
        "codice fiscale": 7,
        "cost of living": 7,
        "flat": 5,
        "health service": 6,
        "housing": 6,
        "linate": 7,
        "malpensa": 7,
        "milan centrale": 6,
        "neighborhood": 5,
        "neighbourhood": 5,
        "permit": 5,
        "rent": 5,
        "residence permit": 7,
        "ssn": 7,
        "transport": 4,
        "visa": 5,
    },
    "life_on_campus": {
        "association": 5,
        "biblioteca": 7,
        "campus": 3,
        "counseling": 5,
        "dining": 7,
        "event": 4,
        "gym": 4,
        "library": 7,
        "mensa": 7,
        "sport": 6,
        "student club": 6,
        "wellbeing": 5,
        "well-being": 5,
    },
    "study_abroad": {
        "abroad": 7,
        "bachelor degree grade": 6,
        "cems": 6,
        "double degree": 8,
        "exchange": 8,
        "free mover": 7,
        "gpa": 4,
        "international opportunity": 7,
        "partner university": 7,
        "selection score": 6,
        "summer school": 7,
    },
    "career_readiness": {
        "almalaurea": 7,
        "award": 4,
        "bess": 5,
        "career": 7,
        "cv": 5,
        "employer": 4,
        "finance": 3,
        "graduate survey": 7,
        "internship": 7,
        "job": 5,
        "merit award": 8,
        "msc": 4,
        "placement": 7,
        "scholarship": 5,
        "tuition waiver": 7,
    },
}

SYSTEM_PROMPT = """You are Bocconi AI Buddy, a concise assistant for Bocconi students.
Answer only from the provided source excerpts. If the excerpts do not support
the answer, say that the available sources do not contain enough information.
Keep the answer in the same language as the student's question. Be especially
careful with dates, deadlines, amounts, counts, and false premises."""


@dataclass(frozen=True)
class SourceDocument:
    path: str
    verticale: Verticale
    title: str
    body: str
    title_search: str
    path_search: str
    search_text: str


@dataclass(frozen=True)
class ScoredSnippet:
    document: SourceDocument
    score: int
    text: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    verticale: Verticale


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return ascii_text.lower()


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [
        token
        for token in TOKEN_RE.findall(normalized)
        if (len(token) >= 3 or (token.isdigit() and len(token) >= 2))
        and token not in STOPWORDS
    ]


def expand_terms(terms: list[str]) -> list[str]:
    expanded: list[str] = []
    seen: set[str] = set()
    for term in terms:
        for candidate in (term, *QUERY_SYNONYMS.get(term, [])):
            normalized = normalize_text(candidate)
            if normalized and normalized not in seen:
                expanded.append(normalized)
                seen.add(normalized)
    return expanded


def compact_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def strip_frontmatter(raw: str) -> str:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return raw.strip()


@lru_cache(maxsize=1)
def load_documents() -> tuple[SourceDocument, ...]:
    manifest_path = DATA_DIR / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    documents: list[SourceDocument] = []
    for item in manifest.get("files", []):
        verticale = item.get("verticale")
        if verticale not in VERTICALS:
            continue

        relative_path = item["path"]
        file_path = DATA_DIR / relative_path
        try:
            raw = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        title = item.get("title") or relative_path
        body = strip_frontmatter(raw)
        title_search = normalize_text(title)
        path_search = normalize_text(relative_path.replace("-", " ").replace("_", " "))
        search_text = normalize_text(f"{title} {relative_path} {body}")
        documents.append(
            SourceDocument(
                path=relative_path,
                verticale=verticale,
                title=title,
                body=body,
                title_search=title_search,
                path_search=path_search,
                search_text=search_text,
            )
        )

    return tuple(documents)


def keyword_score(text: str, keywords: dict[str, int]) -> int:
    normalized = normalize_text(text)
    tokens = set(tokenize(text))
    score = 0
    for keyword, weight in keywords.items():
        normalized_keyword = normalize_text(keyword)
        if " " in normalized_keyword or "-" in normalized_keyword:
            if normalized_keyword in normalized:
                score += weight
        elif normalized_keyword in tokens:
            score += weight
    return score


def score_document(document: SourceDocument, terms: list[str], phrases: list[str]) -> int:
    score = 0
    for phrase in phrases:
        if phrase in document.title_search:
            score += 30
        if phrase in document.path_search:
            score += 20
        if phrase in document.search_text:
            score += 12

    for term in terms:
        if term in document.title_search:
            score += 12
        if term in document.path_search:
            score += 8
        count = document.search_text.count(term)
        if count:
            score += min(count, 10)

    return score


def make_phrases(terms: list[str]) -> list[str]:
    phrases: list[str] = []
    for size in (3, 2):
        for index in range(0, max(len(terms) - size + 1, 0)):
            phrase = " ".join(terms[index : index + size])
            if len(phrase) >= 8:
                phrases.append(phrase)
    return phrases


def classify_verticale(question: str) -> Verticale:
    keyword_scores = {
        verticale: keyword_score(question, keywords)
        for verticale, keywords in VERTICAL_KEYWORDS.items()
    }
    best_verticale = max(keyword_scores, key=keyword_scores.get)
    if keyword_scores[best_verticale] > 0:
        return best_verticale

    terms = expand_terms(tokenize(question))
    phrases = make_phrases(tokenize(question))
    document_scores = dict.fromkeys(VERTICALS, 0)
    for document in load_documents():
        score = score_document(document, terms, phrases)
        if score > 0:
            document_scores[document.verticale] += score

    best_document_verticale = max(document_scores, key=document_scores.get)
    if document_scores[best_document_verticale] > 0:
        return best_document_verticale

    return "life_on_campus"


def best_snippet(document: SourceDocument, terms: list[str], max_chars: int = 1600) -> str:
    paragraphs = [
        compact_text(paragraph)
        for paragraph in re.split(r"\n\s*\n", document.body)
        if compact_text(paragraph)
    ]
    scored: list[tuple[int, str]] = []
    for paragraph in paragraphs:
        paragraph_search = normalize_text(paragraph)
        score = sum(min(paragraph_search.count(term), 5) for term in terms)
        if score > 0:
            scored.append((score, paragraph))

    if not scored:
        return compact_text(document.body[:max_chars])

    scored.sort(key=lambda item: item[0], reverse=True)
    selected: list[str] = []
    current_length = 0
    for _, paragraph in scored[:4]:
        remaining = max_chars - current_length
        if remaining <= 120:
            break
        clipped = paragraph[:remaining]
        selected.append(clipped)
        current_length += len(clipped) + 2

    return "\n\n".join(selected)


def retrieve_snippets(
    question: str, verticale: Verticale, limit: int = 6
) -> tuple[Verticale, list[ScoredSnippet]]:
    terms = expand_terms(tokenize(question))
    phrases = make_phrases(tokenize(question))
    documents = load_documents()

    def rank(candidates: list[SourceDocument]) -> list[ScoredSnippet]:
        snippets: list[ScoredSnippet] = []
        for document in candidates:
            score = score_document(document, terms, phrases)
            if score <= 0:
                continue
            snippets.append(
                ScoredSnippet(
                    document=document,
                    score=score,
                    text=best_snippet(document, terms),
                )
            )
        snippets.sort(key=lambda snippet: snippet.score, reverse=True)
        return snippets[:limit]

    selected = [document for document in documents if document.verticale == verticale]
    snippets = rank(selected)
    if snippets:
        return verticale, snippets

    fallback_snippets = rank(list(documents))
    if fallback_snippets:
        return fallback_snippets[0].document.verticale, fallback_snippets

    return verticale, []


def build_context(snippets: list[ScoredSnippet]) -> str:
    context_blocks: list[str] = []
    for index, snippet in enumerate(snippets, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[{index}] {snippet.document.path}",
                    f"Title: {snippet.document.title}",
                    "Excerpt:",
                    snippet.text,
                ]
            )
        )
    return "\n\n---\n\n".join(context_blocks)


def fallback_answer(reason: str) -> str:
    return (
        "I cannot answer right now from the available sources. "
        f"{reason}"
    )


def generate_answer(
    question: str, verticale: Verticale, snippets: list[ScoredSnippet]
) -> str:
    if not snippets:
        return (
            "I do not have enough information in the available Bocconi sources "
            "to answer this reliably."
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return fallback_answer("The OpenAI API key is not configured.")

    model = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
    timeout = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "20"))
    client = OpenAI(api_key=api_key, timeout=timeout)
    user_input = f"""Question:
{question}

Detected verticale: {verticale}

Source excerpts:
{build_context(snippets)}
"""

    try:
        response = client.responses.create(
            model=model,
            instructions=SYSTEM_PROMPT,
            input=user_input,
            max_output_tokens=900,
        )
    except OpenAIError as exc:
        return fallback_answer(f"OpenAI returned an error: {exc.__class__.__name__}.")
    except Exception:
        # Keep /ask resilient and return a graceful answer instead of 500.
        return fallback_answer("An unexpected model error occurred.")

    answer = getattr(response, "output_text", "").strip()
    if answer:
        return answer

    return fallback_answer("OpenAI returned an empty answer.")


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    question = request.question.strip()
    if not question:
        return AskResponse(
            answer="Please provide a non-empty question.",
            sources=[],
            verticale="life_on_campus",
        )

    verticale = classify_verticale(question)
    verticale, snippets = retrieve_snippets(question, verticale)
    answer = generate_answer(question, verticale, snippets)

    return AskResponse(
        answer=answer,
        sources=[snippet.document.path for snippet in snippets],
        verticale=verticale,
    )
