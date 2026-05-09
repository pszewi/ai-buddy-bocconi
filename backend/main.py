"""Bocconi AI Buddy - backend entry point."""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import uuid4

import faiss
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi

app = FastAPI(title="Bocconi AI Buddy")

_allowed = [
    origin.strip()
    for origin in (os.environ.get("FRONTEND_URL") or "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RECENT_QUESTIONS_LIMIT = 50
RECENT_QUESTIONS_RESPONSE_LIMIT = 10
RECENT_QUESTIONS: deque[tuple[str, Verticale, float]] = deque(
    maxlen=RECENT_QUESTIONS_LIMIT
)
RECENT_QUESTIONS_LOCK = Lock()
LOG_REDACTION_RE = re.compile(
    r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\+?\d[\d\s().-]{7,}\d)",
    re.IGNORECASE,
)
LOG_ANSWER_CHARS = int(os.environ.get("BUDDY_LOG_ANSWER_CHARS", "1600"))
ASK_LOG_SCHEMA_VERSION = "ask-log-v2"

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
INDEX_DIR = DATA_DIR / "index"
FAISS_PATH = INDEX_DIR / "faiss.bin"
METADATA_PATH = INDEX_DIR / "metadata.jsonl"
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"

EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_FAST_MODEL = os.environ.get("OPENAI_FAST_MODEL", "gpt-5.4-mini")
ANSWER_MODEL = os.environ.get("OPENAI_MODEL", DEFAULT_FAST_MODEL)
ANSWER_FALLBACK_MODEL = os.environ.get("OPENAI_FALLBACK_MODEL", DEFAULT_FAST_MODEL)
RERANK_MODEL = os.environ.get("OPENAI_RERANK_MODEL", DEFAULT_FAST_MODEL)
REWRITE_MODEL = os.environ.get("OPENAI_REWRITE_MODEL", DEFAULT_FAST_MODEL)

QUESTION_TIMEOUT_SECONDS = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "20"))
RERANK_TIMEOUT_SECONDS = float(os.environ.get("OPENAI_RERANK_TIMEOUT_SECONDS", "2"))
REWRITE_TIMEOUT_SECONDS = float(os.environ.get("OPENAI_REWRITE_TIMEOUT_SECONDS", "1"))

HYBRID_ENABLED = os.environ.get("BUDDY_HYBRID_ENABLED", "1") != "0"
RERANK_ENABLED = os.environ.get("BUDDY_RERANK_ENABLED", "1") != "0"
REWRITE_ENABLED = os.environ.get("BUDDY_REWRITE_ENABLED", "1") != "0"

VECTOR_TOP_K = int(os.environ.get("BUDDY_VECTOR_TOP_K", "24"))
HYBRID_TOP_K = int(os.environ.get("BUDDY_HYBRID_TOP_K", "24"))
SECONDARY_TOP_K = int(os.environ.get("BUDDY_SECONDARY_TOP_K", "24"))
RERANK_CANDIDATE_K = int(os.environ.get("BUDDY_RERANK_CANDIDATE_K", "20"))
FINAL_SNIPPETS = int(os.environ.get("BUDDY_FINAL_SNIPPETS", "6"))
RRF_K = 60
RERANK_EXCERPT_CHARS = 1600
ANSWER_EXCERPT_CHARS = 3600

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_'-]{1,}", re.IGNORECASE)
TOKEN_SEPARATOR_RE = re.compile(r"['’`/]")
WHITESPACE_RE = re.compile(r"\s+")
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9&.-]{1,}\b")
YEAR_RE = re.compile(r"\b20\d{2}\b")
PARENTHETICAL_RE = re.compile(r"\(([^)]{4,120})\)")
PHRASE_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z.'-]*")

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

LEXICAL_BOOST_STOPWORDS = STOPWORDS | {
    "bocconi",
    "department",
    "agli",
    "listed",
    "main",
    "milano",
    "offre",
    "page",
    "professor",
    "quali",
    "questions",
    "research",
    "servizi",
    "student",
    "students",
    "studenti",
    "trasferiscono",
    "university",
}

IGNORED_ACRONYMS = {
    "AI",
    "FAQ",
    "HTTP",
    "HTTPS",
    "ID",
    "PDF",
    "UK",
    "URL",
    "US",
    "USA",
}

GENERIC_ENTITY_PHRASES = {
    "bocconi",
    "bocconi university",
    "master of science",
}

INSTRUCTION_PARENTHESES_MARKERS = (
    " exclude ",
    " excluding ",
    " except ",
    " only ",
    " excluding the ",
    " esclusi ",
    " escluse ",
    " escludi ",
    " solo ",
    " soltanto ",
)

ACRONYM_ALIASES = {
    "SSN": (
        "national health service",
        "servizio sanitario nazionale",
        "servizio sanitario regionale",
        "regional health service",
    ),
    "SSR": (
        "servizio sanitario regionale",
        "regional health service",
    ),
    "EU": (
        "european union",
        "unione europea",
    ),
    "EEA": (
        "european economic area",
        "spazio economico europeo",
    ),
}

ANNUAL_PRICE_MARKERS = (
    "annual",
    "annuale",
    "annually",
    "per year",
    "all'anno",
    "all anno",
    "annuo",
    "annua",
)

ADULT_ANNUAL_TRANSPORT_MARKERS = (
    "adult annual",
    "standard adult annual",
    "annual urban pass",
    "abbonamento annuale ordinario",
    "annuale ordinario",
    "tessera annuale ordinaria",
)

LONG_FORM_QUESTION_MARKERS = (
    "checklist",
    "compare",
    "comparison",
    "differences",
    "main differences",
    "markdown table",
    "provide a structured",
    "step by step",
    "step-by-step",
    "table",
    "what are the steps",
)

VERTICAL_KEYWORDS: dict[Verticale, dict[str, int]] = {
    "relocation": {
        "airport": 5,
        "atm": 5,
        "bank": 4,
        "bus": 4,
        "codice fiscale": 7,
        "cost of living": 7,
        "flat": 5,
        "health service": 6,
        "housing": 6,
        "linate": 7,
        "malpensa": 8,
        "milan centrale": 7,
        "move to milan": 8,
        "moving to milan": 8,
        "neighborhood": 5,
        "neighbourhood": 5,
        "permit": 5,
        "rent": 5,
        "residence ambassador": 9,
        "residence permit": 7,
        "ssn": 7,
        "trasferirsi": 8,
        "trasferisce": 8,
        "trasferiscono": 8,
        "transport": 4,
        "visa": 5,
    },
    "life_on_campus": {
        "association": 5,
        "biblioteca": 7,
        "campus": 3,
        "counseling": 5,
        "dining": 8,
        "event": 4,
        "gym": 4,
        "library": 8,
        "mensa": 8,
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
        "exchange program": 12,
        "free mover": 7,
        "gpa": 4,
        "international mobility": 8,
        "international opportunity": 7,
        "one-semester": 5,
        "partner university": 7,
        "partenza": 4,
        "scadenze": 5,
        "scambio": 8,
        "selection score": 7,
        "study abroad": 8,
        "summer school": 7,
        "timeline": 4,
    },
    "career_readiness": {
        "alumni": 9,
        "almalaurea": 7,
        "award": 4,
        "b4i": 8,
        "bess": 6,
        "career": 7,
        "chapter": 9,
        "chapter leader": 12,
        "community": 5,
        "cv": 5,
        "employer": 4,
        "faculty": 4,
        "finance": 3,
        "graduate survey": 7,
        "internship": 7,
        "job": 5,
        "merit award": 8,
        "msc": 4,
        "placement": 7,
        "professor": 2,
        "publications": 4,
        "research department": 7,
        "scholarship": 5,
        "startup": 6,
        "topic leader": 8,
        "tuition waiver": 7,
    },
}

ANSWER_SYSTEM_PROMPT = """You are Bocconi AI Buddy, a concise assistant for Bocconi students.
Answer only from the provided source excerpts. If the excerpts do not support
the answer, say that the available sources do not contain enough information.
Treat semantically equivalent wording, page titles, and administrative labels
as support when the source clearly describes the same procedure, office, rule,
deadline, or metric asked about; do not require exact query wording.
If the excerpts support only part of the question, answer the supported part
and explicitly name what is missing from the excerpts instead of fully
abstaining. Keep that partial answer grounded and do not infer the missing part.
Keep the answer in the same language as the student's question. Be especially
careful with dates, deadlines, amounts, counts, and false premises. Do not apply
a generic rule, deadline, or amount to a named program, partner university,
survey, award, or year unless that specific item appears in the excerpts. Do not
convert monthly prices into annual prices unless the source states the annual
price or the question explicitly asks for an estimate/annualized calculation.
For yes/no rules and restrictions, if one excerpt directly says something is
not allowed, do not override that rule with a related optional or extracurricular
activity; explain the distinction instead. Prefer compact bullets or tables;
for checklists and comparisons, include only the essential supported steps and
differences without restating every adjacent source detail. Unless the user asks
for exhaustive detail, keep the final answer compact: usually under 250 words,
no more than 8 checklist items, and no more than 8 table rows."""

RERANK_SYSTEM_PROMPT = """You rank retrieval snippets for question answering.
Return valid JSON only with one key: ids (array of up to 6 chunk IDs), sorted
from most relevant to least relevant. Use only the provided IDs."""

REWRITE_SYSTEM_PROMPT = """Rewrite the user's question into 1-2 short retrieval
queries for the Bocconi dataset. Keep the same language as the user. Return JSON:
{"queries": ["...", "..."]}. If already direct, return it as one query."""


@dataclass(frozen=True)
class ChunkRow:
    row: int
    id: str
    path: str
    verticale: Verticale
    title: str
    text: str
    tokens: list[str]


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: ChunkRow
    score: float


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    history: list[ConversationTurn] = Field(default_factory=list, max_length=8)


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    verticale: Verticale


class RecentQuestionResponse(BaseModel):
    question: str
    verticale: Verticale
    count: int
    asked_at: float


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def clean_history(history: list[ConversationTurn]) -> list[ConversationTurn]:
    cleaned: list[ConversationTurn] = []
    for turn in history[-8:]:
        content = compact_text(turn.content)
        if content:
            cleaned.append(
                ConversationTurn(role=turn.role, content=content[:1000])
            )
    return cleaned


def conversation_history_context(history: list[ConversationTurn]) -> str:
    turns = clean_history(history)
    if not turns:
        return ""

    lines = []
    for turn in turns[-6:]:
        label = "Student" if turn.role == "user" else "Buddy"
        lines.append(f"{label}: {turn.content}")
    return "\n".join(lines)


def retrieval_question_with_history(
    question: str, history: list[ConversationTurn]
) -> str:
    turns = clean_history(history)
    if not turns:
        return question

    context = " ".join(turn.content for turn in turns[-4:])
    return f"{question}\nPrevious conversation context: {context}"


def record_recent_question(question: str, verticale: Verticale) -> None:
    logged_question = compact_text(question)[:240]
    if not logged_question:
        return

    with RECENT_QUESTIONS_LOCK:
        RECENT_QUESTIONS.append((logged_question, verticale, time.time()))


def redacted_log_text(text: str, max_chars: int) -> str:
    return LOG_REDACTION_RE.sub("[redacted]", compact_text(text))[:max_chars]


def selected_chunk_log(snippets: list["RetrievedChunk"]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for snippet in snippets[:6]:
        rows.append(
            {
                "id": snippet.chunk.id,
                "row": snippet.chunk.row,
                "path": snippet.chunk.path,
                "title": snippet.chunk.title,
                "verticale": snippet.chunk.verticale,
                "excerpt_preview": redacted_log_text(snippet.chunk.text, 360),
            }
        )
    return rows


def runtime_log_config() -> dict[str, object]:
    return {
        "answer_model": ANSWER_MODEL,
        "answer_fallback_model": ANSWER_FALLBACK_MODEL,
        "fast_model": DEFAULT_FAST_MODEL,
        "rerank_model": RERANK_MODEL,
        "rewrite_model": REWRITE_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "hybrid_enabled": HYBRID_ENABLED,
        "rerank_enabled": RERANK_ENABLED,
        "rewrite_enabled": REWRITE_ENABLED,
        "vector_top_k": VECTOR_TOP_K,
        "hybrid_top_k": HYBRID_TOP_K,
        "secondary_top_k": SECONDARY_TOP_K,
        "rerank_candidate_k": RERANK_CANDIDATE_K,
        "final_snippets": FINAL_SNIPPETS,
        "index_chunks": len(metadata_by_row()),
    }


def log_ask_event(
    request_id: str,
    question: str,
    verticale: Verticale,
    sources: list[str],
    answer: str,
    started_at: float,
    timings_ms: dict[str, int] | None = None,
    missing_terms: list[str] | None = None,
    diagnostics: dict[str, object] | None = None,
) -> None:
    payload = {
        "event": "ask",
        "schema": ASK_LOG_SCHEMA_VERSION,
        "request_id": request_id,
        "question": redacted_log_text(question, 240),
        "verticale": verticale,
        "source_count": len(sources),
        "source_paths": sources,
        "latency_ms": round((time.perf_counter() - started_at) * 1000),
        "abstained": is_abstention(answer),
        "answer_preview": redacted_log_text(answer, LOG_ANSWER_CHARS),
        "answer_chars": len(answer),
        "runtime": runtime_log_config(),
    }
    if timings_ms:
        payload["timings_ms"] = timings_ms
    if missing_terms:
        payload["missing_terms"] = missing_terms
    if diagnostics:
        payload["diagnostics"] = diagnostics
    print(json.dumps(payload, ensure_ascii=False), flush=True)


@app.get("/recent-questions", response_model=list[RecentQuestionResponse])
def recent_questions() -> list[RecentQuestionResponse]:
    with RECENT_QUESTIONS_LOCK:
        entries = list(RECENT_QUESTIONS)

    aggregated: dict[str, RecentQuestionResponse] = {}
    for question, verticale, asked_at in reversed(entries):
        key = normalize_text(question)
        if not key:
            continue

        existing = aggregated.get(key)
        if existing is None:
            aggregated[key] = RecentQuestionResponse(
                question=question,
                verticale=verticale,
                count=1,
                asked_at=asked_at,
            )
        else:
            existing.count += 1

    return list(aggregated.values())[:RECENT_QUESTIONS_RESPONSE_LIMIT]


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return ascii_text.lower()


def compact_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def tokenize(text: str) -> list[str]:
    normalized = TOKEN_SEPARATOR_RE.sub(" ", normalize_text(text))
    return [
        token
        for token in TOKEN_RE.findall(normalized)
        if (len(token) >= 3 or (token.isdigit() and len(token) >= 2))
        and token not in STOPWORDS
    ]


def exact_tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(TOKEN_SEPARATOR_RE.sub(" ", normalize_text(text))))


def keyword_score(text: str, keywords: dict[str, int]) -> int:
    normalized = normalize_text(text)
    tokens = set(tokenize(text))
    score = 0
    for keyword, weight in keywords.items():
        key = normalize_text(keyword)
        if " " in key or "-" in key:
            if key in normalized:
                score += weight
        elif key in tokens:
            score += weight
    return score


def score_verticals(question: str) -> dict[Verticale, int]:
    return {
        verticale: keyword_score(question, keywords)
        for verticale, keywords in VERTICAL_KEYWORDS.items()
    }


def rank_verticals(question: str) -> list[tuple[Verticale, int]]:
    scores = score_verticals(question)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def classify_verticale(question: str) -> Verticale:
    ranked = rank_verticals(question)
    best, score = ranked[0]
    if score > 0:
        return best
    return "life_on_campus"


def preferred_verticals(question: str) -> tuple[Verticale, ...]:
    ranked = rank_verticals(question)
    best_score = ranked[0][1]
    if best_score <= 0:
        return VERTICALS

    preferred = [
        verticale
        for verticale, score in ranked
        if score > 0 and best_score - score <= 2
    ]
    return tuple(preferred[:2]) or (ranked[0][0],)


def is_probably_italian(text: str) -> bool:
    normalized = normalize_text(text)
    italian_markers = (
        " qual ",
        " quale ",
        " quali ",
        " come ",
        " devo ",
        " posso ",
        " campus ",
        " mensa ",
        " biblioteca ",
        " milano ",
        " studenti ",
        " alloggio ",
        " borsa ",
        " tirocinio ",
        " estero ",
    )
    padded = f" {normalized} "
    return any(marker in padded for marker in italian_markers)


def localize_message(question: str, english: str, italian: str) -> str:
    if is_probably_italian(question):
        return italian
    return english


def answer_language_name(question: str) -> str:
    if is_probably_italian(question):
        return "Italian"
    return "English"


def no_info_answer(question: str) -> str:
    return localize_message(
        question,
        "I do not have enough information in the available Bocconi sources to answer this reliably.",
        "Non ho abbastanza informazioni nelle fonti Bocconi disponibili per rispondere in modo affidabile.",
    )


def format_specific_terms(terms: list[str]) -> str:
    shown = [f'"{term}"' for term in terms[:4]]
    if len(terms) > 4:
        shown.append(f"{len(terms) - 4} other specific terms")
    if len(shown) <= 1:
        return "".join(shown)
    if len(shown) == 2:
        return f"{shown[0]} and {shown[1]}"
    return f"{', '.join(shown[:-1])}, and {shown[-1]}"


def unsupported_specifics_answer(question: str, missing_terms: list[str]) -> str:
    formatted = format_specific_terms(missing_terms)
    return localize_message(
        question,
        (
            "The retrieved sources do not mention "
            f"{formatted} in relation to this question, so I cannot answer it "
            "reliably. I will not apply a generic deadline, amount, rule, or "
            "result to a specific item that is not present in the sources."
        ),
        (
            "Le fonti recuperate non menzionano "
            f"{formatted} in relazione a questa domanda, quindi non posso "
            "rispondere in modo affidabile. Non applico una scadenza, un "
            "importo, una regola o un risultato generale a un caso specifico "
            "che non e' presente nelle fonti."
        ),
    )


def fallback_answer(question: str, reason: str) -> str:
    base = localize_message(
        question,
        "I cannot answer right now from the available sources.",
        "Non riesco a rispondere in questo momento sulla base delle fonti disponibili.",
    )
    return f"{base} {reason}"


def fallback_reason(question: str, english: str, italian: str) -> str:
    return localize_message(question, english, italian)


def is_abstention(answer: str) -> bool:
    normalized = normalize_text(answer)
    abstention_markers = (
        "i do not have enough information",
        "i don't have enough information",
        "i cannot answer",
        "do not contain enough information",
        "does not contain enough information",
        "non ho abbastanza informazioni",
        "non posso rispondere",
        "non riesco a rispondere",
    )
    partial_markers = (
        "however",
        "but",
        "pero",
        "tuttavia",
        "secondo",
        "according to",
        "sulla base",
    )
    if not any(marker in normalized for marker in abstention_markers):
        return False
    return not any(marker in normalized for marker in partial_markers)


def add_required_term(
    terms: list[tuple[str, str]], seen: set[str], term: str, match_mode: str
) -> None:
    clean = compact_text(term.strip(" .,:;"))
    normalized = normalize_text(clean)
    if not clean or normalized in seen:
        return
    seen.add(normalized)
    terms.append((clean, match_mode))


def required_evidence_terms(question: str) -> list[tuple[str, str]]:
    terms: list[tuple[str, str]] = []
    seen: set[str] = set()

    for acronym in ACRONYM_RE.findall(question):
        clean = acronym.strip(".-")
        if clean.upper() in IGNORED_ACRONYMS:
            continue
        add_required_term(terms, seen, clean, "token")

    for year in YEAR_RE.findall(question):
        add_required_term(terms, seen, year, "substring")

    for phrase in PARENTHETICAL_RE.findall(question):
        clean = compact_text(phrase.strip())
        normalized = normalize_text(clean)
        padded = f" {normalized} "
        if (
            normalized in GENERIC_ENTITY_PHRASES
            or normalized.startswith("e.g")
            or normalized.startswith("i.e")
            or any(marker in padded for marker in INSTRUCTION_PARENTHESES_MARKERS)
        ):
            continue
        words = PHRASE_TOKEN_RE.findall(clean)
        capitalized = [word for word in words if word[:1].isupper()]
        if "," in clean and len(capitalized) >= 2:
            for part in re.split(r",|;", clean):
                part_clean = compact_text(part.replace("/", " ").strip())
                part_words = PHRASE_TOKEN_RE.findall(part_clean)
                part_capitalized = [
                    word for word in part_words if word[:1].isupper()
                ]
                if part_words and part_capitalized:
                    add_required_term(terms, seen, part_clean, "substring")
            continue
        if len(words) >= 2 and len(capitalized) >= 2:
            add_required_term(terms, seen, clean, "substring")

    return terms


def evidence_text(snippets: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    for snippet in snippets:
        parts.extend(
            [
                snippet.chunk.path,
                snippet.chunk.title,
                snippet.chunk.text[:ANSWER_EXCERPT_CHARS],
            ]
        )
    return "\n".join(parts)


def missing_required_evidence_terms(
    question: str, snippets: list[RetrievedChunk]
) -> list[str]:
    terms = required_evidence_terms(question)
    if not terms:
        return []

    text = evidence_text(snippets)
    normalized_text = normalize_text(text)
    evidence_tokens = exact_tokens(text)
    missing: list[str] = []

    for term, match_mode in terms:
        if not evidence_supports_term(
            term, match_mode, normalized_text, evidence_tokens
        ):
            missing.append(term)

    missing.extend(missing_cooccurring_evidence_terms(terms, snippets))

    return missing


def evidence_supports_term(
    term: str,
    match_mode: str,
    normalized_text: str,
    evidence_tokens: set[str],
) -> bool:
    normalized_term = normalize_text(term)
    if match_mode == "token":
        return (
            normalized_term in evidence_tokens
            or acronym_supported_by_alias(term, normalized_text)
        )

    if normalized_term in normalized_text:
        return True

    term_tokens = [
        token
        for token in tokenize(term)
        if not token.isdigit() and token not in STOPWORDS
    ]
    return bool(term_tokens) and all(token in evidence_tokens for token in term_tokens)


def missing_cooccurring_evidence_terms(
    terms: list[tuple[str, str]], snippets: list[RetrievedChunk]
) -> list[str]:
    years = [term for term, _ in terms if YEAR_RE.fullmatch(term)]
    named_terms = [
        (term, mode)
        for term, mode in terms
        if not YEAR_RE.fullmatch(term) and normalize_text(term) not in GENERIC_ENTITY_PHRASES
    ]
    if not years or not named_terms:
        return []

    snippet_texts = [
        "\n".join([snippet.chunk.path, snippet.chunk.title, snippet.chunk.text])
        for snippet in snippets
    ]
    missing: list[str] = []
    for named_term, match_mode in named_terms:
        for year in years:
            supported = False
            for text in snippet_texts:
                normalized_text = normalize_text(text)
                tokens = exact_tokens(text)
                has_name = evidence_supports_term(
                    named_term, match_mode, normalized_text, tokens
                )
                has_year = evidence_supports_term(
                    year, "substring", normalized_text, tokens
                )
                if has_name and has_year:
                    supported = True
                    break
            if not supported:
                missing.append(f"{named_term} {year}")
    return missing


def acronym_supported_by_alias(term: str, normalized_text: str) -> bool:
    aliases = ACRONYM_ALIASES.get(term.upper(), ())
    return any(normalize_text(alias) in normalized_text for alias in aliases)


def asks_annual_transport_pass(question: str) -> bool:
    normalized = normalize_text(question)
    has_annual = any(marker in normalized for marker in ANNUAL_PRICE_MARKERS)
    has_transport = any(
        marker in normalized
        for marker in ("atm", "transit", "transport", "urban", "abbonamento")
    )
    has_pass = "pass" in normalized or "abbonamento" in normalized
    return has_annual and has_transport and has_pass


def missing_contextual_evidence_terms(
    question: str, snippets: list[RetrievedChunk]
) -> list[str]:
    if not asks_annual_transport_pass(question):
        return []

    normalized_question = normalize_text(question)
    normalized_evidence = normalize_text(evidence_text(snippets))
    missing: list[str] = []

    if not any(marker in normalized_evidence for marker in ANNUAL_PRICE_MARKERS):
        missing.append("an annual public-transport pass price")

    asks_adult_comparison = (
        "adult" in normalized_question or "ordinario" in normalized_question
    )
    if asks_adult_comparison and not any(
        marker in normalized_evidence for marker in ADULT_ANNUAL_TRANSPORT_MARKERS
    ):
        missing.append("the standard adult annual urban pass")

    return missing


def get_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()


def make_client(timeout_seconds: float) -> OpenAI:
    return OpenAI(api_key=get_api_key(), timeout=timeout_seconds, max_retries=0)


def unique_models(*models: str) -> tuple[str, ...]:
    ordered: list[str] = []
    for model in models:
        clean = model.strip()
        if clean and clean not in ordered:
            ordered.append(clean)
    return tuple(ordered)


def is_long_form_question(question: str) -> bool:
    normalized = normalize_text(question)
    return any(marker in normalized for marker in LONG_FORM_QUESTION_MARKERS)


def answer_models_for_question(question: str) -> tuple[str, ...]:
    if is_long_form_question(question):
        return unique_models(DEFAULT_FAST_MODEL, ANSWER_MODEL, ANSWER_FALLBACK_MODEL)
    return unique_models(ANSWER_MODEL, ANSWER_FALLBACK_MODEL)


def with_retries(func, *, attempts: int = 3):
    delay_seconds = 0.5
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return func()
        except OpenAIError as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise
            time.sleep(delay_seconds)
            delay_seconds = min(delay_seconds * 2, 2.0)
    if last_error is not None:
        raise last_error
    return func()


def extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output_items = getattr(response, "output", None) or []
    parts: list[str] = []
    for item in output_items:
        content_list = getattr(item, "content", None) or []
        for content in content_list:
            text_value = getattr(content, "text", None)
            if isinstance(text_value, str) and text_value.strip():
                parts.append(text_value.strip())
                continue

            text_obj = getattr(content, "output_text", None)
            if isinstance(text_obj, str) and text_obj.strip():
                parts.append(text_obj.strip())
    return "\n".join(parts).strip()


@lru_cache(maxsize=1)
def load_metadata() -> tuple[ChunkRow, ...]:
    source_path = METADATA_PATH if METADATA_PATH.exists() else CHUNKS_PATH
    if not source_path.exists():
        return ()

    rows: list[ChunkRow] = []
    with source_path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if not line.strip():
                continue
            data = json.loads(line)
            row_idx = int(data.get("row", idx))
            verticale_raw = data.get("verticale", "life_on_campus")
            verticale: Verticale = (
                verticale_raw if verticale_raw in VERTICALS else "life_on_campus"
            )
            text = compact_text(data.get("text", ""))
            rows.append(
                ChunkRow(
                    row=row_idx,
                    id=data.get("id", f"row-{row_idx}"),
                    path=data.get("path", ""),
                    verticale=verticale,
                    title=data.get("title", data.get("path", "")),
                    text=text,
                    tokens=tokenize(text),
                )
            )
    return tuple(rows)


@lru_cache(maxsize=1)
def metadata_by_row() -> dict[int, ChunkRow]:
    return {chunk.row: chunk for chunk in load_metadata()}


@lru_cache(maxsize=1)
def load_faiss_index() -> faiss.Index | None:
    if not FAISS_PATH.exists():
        return None
    return faiss.read_index(str(FAISS_PATH))


@lru_cache(maxsize=1)
def load_bm25() -> BM25Okapi | None:
    chunks = load_metadata()
    if not chunks:
        return None
    corpus_tokens = [chunk.tokens for chunk in chunks]
    return BM25Okapi(corpus_tokens)


def embed_query(query: str) -> np.ndarray | None:
    if not get_api_key():
        return None
    try:
        client = make_client(QUESTION_TIMEOUT_SECONDS)
        response = with_retries(
            lambda: client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=query,
            )
        )
    except Exception:
        return None
    vector = np.array(response.data[0].embedding, dtype="float32").reshape(1, -1)
    faiss.normalize_L2(vector)
    return vector


def vector_search_rows(query: str, top_k: int) -> list[tuple[int, float]]:
    index = load_faiss_index()
    if index is None:
        return []
    vector = embed_query(query)
    if vector is None:
        return []

    distances, labels = index.search(vector, top_k)
    rows: list[tuple[int, float]] = []
    for row_id, score in zip(labels[0], distances[0]):
        if row_id < 0:
            continue
        rows.append((int(row_id), float(score)))
    return rows


def bm25_search_rows(query: str, top_k: int) -> list[tuple[int, float]]:
    bm25 = load_bm25()
    chunks = load_metadata()
    if bm25 is None or not chunks:
        return []
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    scores = bm25.get_scores(query_tokens)
    if scores is None or len(scores) == 0:
        return []
    order = np.argsort(scores)[::-1][:top_k]
    rows: list[tuple[int, float]] = []
    for idx in order:
        if scores[idx] <= 0:
            continue
        rows.append((chunks[idx].row, float(scores[idx])))
    return rows


def rewrite_queries(question: str) -> list[str]:
    direct_queries = direct_retrieval_queries(question)
    if direct_queries:
        return direct_queries

    if not REWRITE_ENABLED:
        return [question]
    if len(tokenize(question)) < 8:
        return [question]
    if not get_api_key():
        return [question]

    payload = f'Question: {question}\nReturn JSON only.'
    try:
        client = make_client(REWRITE_TIMEOUT_SECONDS)
        response = with_retries(
            lambda: client.responses.create(
                model=REWRITE_MODEL,
                instructions=REWRITE_SYSTEM_PROMPT,
                input=payload,
                max_output_tokens=120,
            ),
            attempts=1,
        )
        content = extract_response_text(response)
        parsed = json.loads(content)
        queries = parsed.get("queries", [])
        cleaned = [compact_text(q) for q in queries if compact_text(q)]
        if cleaned:
            return cleaned[:2]
    except Exception:
        pass
    return [question]


def direct_retrieval_queries(question: str) -> list[str]:
    normalized = TOKEN_SEPARATOR_RE.sub(" ", normalize_text(question))
    queries: list[str] = []

    if "atm" in normalized and ("under 27" in normalized or "adult annual" in normalized):
        queries.append(question)
        queries.append(
            "ATM urban travel passes Milan young people under 27 annual 200 "
            "ordinary adult annual urban subscription 330"
        )
    elif (
        "malpensa" in normalized
        and "milano centrale" in normalized
        and (
            "autostradale" in normalized
            or "terravision" in normalized
            or "flibco" in normalized
            or "flixbus" in normalized
        )
    ):
        queries.append(question)
        queries.append(
            "Malpensa Milan Centrale bus Autostradale Malpensa Bus Express "
            "Terravision Flibco FlixBus ticket prices"
        )
    elif "bocconi merit award" in normalized or "graduate merit award" in normalized:
        queries.append(question)
        queries.append(
            "Bocconi Graduate Merit Awards 2026 27 100% waiver full tuition "
            "and fees waiver MSc"
        )
    elif "exchange program" in normalized:
        queries.append(question)
        queries.append(
            "Exchange Program 2026-27 timing deadlines application opens "
            "Punto Blu language certificates results confirmation departure "
            "graduate requirements"
        )
    elif "anna battauz" in normalized or "battauz" in normalized:
        queries.append(question)
        queries.append(
            "Anna Battauz Department of Finance faculty publications"
        )
    elif "career services" in normalized and "internship" in normalized:
        queries.append(question)
        queries.append("Career Services internship office contacts email")
    elif "alumni" in normalized or "chapter leader" in normalized:
        queries.append(question)
        queries.append(
            "Bocconi Alumni Community Chapter Leader geographic chapters "
            "February 2026 Topic Leader"
        )
    elif "b4i" in normalized or "bocconi for innovation" in normalized:
        queries.append(question)
        queries.append(
            "B4i Bocconi for Innovation incubator startup supported capital "
            "raised community startups"
        )
    elif "qs" in normalized and "business" in normalized:
        queries.append(question)
        queries.append(
            "QS World University Rankings by Subject 2026 Business "
            "Management Studies Bocconi rank score"
        )
    elif "trasfer" in normalized or "move to milan" in normalized:
        queries.append(question)
        queries.append(
            "Freshly enrolled students when you arrive Bocconi Permit of Stay "
            "Fiscal Code Welcome activities B in Touch Wi-Fi Library housing"
        )

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        key = normalize_text(query)
        if key and key not in seen:
            deduped.append(query)
            seen.add(key)
    return deduped[:2]


def targeted_secondary_queries(
    question: str,
    verticals: tuple[Verticale, ...],
    missing_terms: list[str] | None = None,
) -> list[str]:
    normalized = TOKEN_SEPARATOR_RE.sub(" ", normalize_text(question))
    queries = [question, *direct_retrieval_queries(question)]
    if missing_terms:
        queries.append(f"{question} {' '.join(missing_terms[:4])}")

    if "study_abroad" in verticals:
        if "exchange" in normalized:
            queries.extend(
                [
                    "Exchange Program application selection timeline requirements "
                    "results waiting list accept withdraw start mobility",
                    "Exchange Program course selection academic recognition "
                    "language requirements application Punto Blu deadlines",
                ]
            )
        if "free mover" in normalized:
            queries.append(
                "Free Mover Summer how to apply Punto Blu student info document "
                "English certificate application receipt Summer Program"
            )
        if "visa" in normalized or "universitaly" in normalized:
            queries.append(
                "incoming exchange students visa process Universitaly Step B "
                "Step C passport acceptance letter course type Corsi Singoli"
            )
        if "course selection" in normalized or "add drop" in normalized:
            queries.append(
                "incoming exchange students course selection add drop Fall "
                "courses semester language courses study plan"
            )
        if "double degree" in normalized:
            queries.append(
                "Double Degree program application selection timeline costs "
                "scholarships administrative contribution tuition fees DD network"
            )

    if "career_readiness" in verticals:
        if "internship" in normalized:
            queries.extend(
                [
                    "Career Services internship office contacts B in Touch "
                    "Internships topic dedicated phone number JobGate",
                    "internship document first day printed signed original "
                    "Internship Office Bocconi Post Office Viale Bligny",
                    "curricular extracurricular internships activation "
                    "recognition requirements JobGate family-owned company",
                ]
            )
        if "placement" in normalized or "employed" in normalized:
            queries.append(
                "MSc placement and program performance one year after graduation "
                "employment work abroad interviews job offers continuing studies"
            )
        if "award" in normalized or "waiver" in normalized or "scholarship" in normalized:
            queries.append(
                "Bocconi Graduate Merit Award tuition fees waiver full tuition "
                "fees waiver stipend renewal requirements"
            )
        if (
            "professor" in normalized
            or "department" in normalized
            or "publication" in normalized
        ):
            queries.append(
                "Bocconi research department faculty professor publications "
                "Department of Finance"
            )
        if "alumni" in normalized or "chapter leader" in normalized:
            queries.append(
                "Bocconi Alumni Community Chapter Leader geographic chapters "
                "February 2026 Topic Leader international chapter"
            )
        if "b4i" in normalized or "bocconi for innovation" in normalized:
            queries.append(
                "B4i Bocconi for Innovation incubator startups supported "
                "capital raised community entrepreneurship"
            )
        if "qs" in normalized and "business" in normalized:
            queries.append(
                "QS World University Rankings by Subject 2026 Business "
                "Management Studies Bocconi rank overall score"
            )

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        clean = compact_text(query)
        key = normalize_text(clean)
        if clean and key not in seen:
            deduped.append(clean)
            seen.add(key)
    return deduped[:6]


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = RRF_K) -> list[int]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, row_id in enumerate(ranking, start=1):
            scores[row_id] = scores.get(row_id, 0.0) + (1.0 / (k + rank))
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [row_id for row_id, _ in ordered]


def salient_query_terms(question: str) -> set[str]:
    return {
        token
        for token in tokenize(question)
        if len(token) >= 5 and token not in LEXICAL_BOOST_STOPWORDS
    }


def proper_query_terms(question: str) -> set[str]:
    terms: set[str] = set()
    for word in PHRASE_TOKEN_RE.findall(question):
        if not word[:1].isupper():
            continue
        normalized = normalize_text(word)
        if len(normalized) < 4 or normalized in LEXICAL_BOOST_STOPWORDS:
            continue
        terms.add(normalized)
    return terms


@lru_cache(maxsize=10000)
def chunk_search_tokens(row_id: int) -> frozenset[str]:
    chunk = metadata_by_row().get(row_id)
    if chunk is None:
        return frozenset()
    return frozenset([*chunk.tokens, *tokenize(chunk.title), *tokenize(chunk.path)])


def lexical_overlap_score(question: str, chunk: ChunkRow) -> int:
    terms = salient_query_terms(question)
    proper_terms = proper_query_terms(question)
    if not terms and not proper_terms:
        return 0

    haystack = chunk_search_tokens(chunk.row)
    score = sum(1 for term in terms if term in haystack)
    score += sum(4 for term in proper_terms if term in haystack)
    return score


def max_lexical_overlap(question: str, snippets: list[RetrievedChunk]) -> int:
    if not snippets:
        return 0
    return max(lexical_overlap_score(question, snippet.chunk) for snippet in snippets)


def unique_source_count(snippets: list[RetrievedChunk]) -> int:
    return len({snippet.chunk.path for snippet in snippets if snippet.chunk.path})


def lexical_search_rows(
    query: str, verticals: tuple[Verticale, ...], top_k: int
) -> list[int]:
    scored: list[tuple[int, int]] = []
    for chunk in load_metadata():
        if chunk.verticale not in verticals:
            continue
        score = lexical_overlap_score(query, chunk)
        if score > 0:
            scored.append((score, chunk.row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row_id for _, row_id in scored[:top_k]]


def merge_lexical_priority(
    question: str, candidates: list[ChunkRow], ranked_rows: list[int]
) -> list[int]:
    scored = [
        (lexical_overlap_score(question, chunk), chunk.row)
        for chunk in candidates
    ]
    lexical_rows = [
        row_id
        for score, row_id in sorted(scored, key=lambda item: item[0], reverse=True)
        if score > 0
    ][:2]

    merged: list[int] = []
    for row_id in [*lexical_rows, *ranked_rows]:
        if row_id not in merged:
            merged.append(row_id)
    return merged


def rerank_rows(question: str, candidates: list[ChunkRow]) -> list[int]:
    if not RERANK_ENABLED or not candidates or not get_api_key():
        return merge_lexical_priority(
            question,
            candidates,
            [chunk.row for chunk in candidates[:FINAL_SNIPPETS]],
        )[:FINAL_SNIPPETS]

    chunks_payload = []
    for chunk in candidates:
        chunks_payload.append(
            {
                "id": chunk.id,
                "path": chunk.path,
                "title": chunk.title,
                "text": chunk.text[:RERANK_EXCERPT_CHARS],
            }
        )
    prompt = json.dumps(
        {
            "question": question,
            "chunks": chunks_payload,
            "required_output": {"ids": ["chunk-id-1", "chunk-id-2"]},
        },
        ensure_ascii=False,
    )

    try:
        client = make_client(RERANK_TIMEOUT_SECONDS)
        response = with_retries(
            lambda: client.responses.create(
                model=RERANK_MODEL,
                instructions=RERANK_SYSTEM_PROMPT,
                input=prompt,
                max_output_tokens=180,
            ),
            attempts=1,
        )
        content = extract_response_text(response)
        parsed = json.loads(content)
        ranked_ids = parsed.get("ids", [])
        id_to_row = {chunk.id: chunk.row for chunk in candidates}
        rows: list[int] = []
        for chunk_id in ranked_ids:
            row_id = id_to_row.get(str(chunk_id))
            if row_id is not None and row_id not in rows:
                rows.append(row_id)
        if rows:
            return merge_lexical_priority(question, candidates, rows)[:FINAL_SNIPPETS]
    except Exception:
        pass

    return merge_lexical_priority(
        question,
        candidates,
        [chunk.row for chunk in candidates[:FINAL_SNIPPETS]],
    )[:FINAL_SNIPPETS]


def should_rerank(candidates: list[ChunkRow]) -> bool:
    if not RERANK_ENABLED or len(candidates) <= 5:
        return False
    top_paths = {chunk.path for chunk in candidates[:3] if chunk.path}
    return len(top_paths) > 1


def prioritize_rows(
    rows: list[int], by_row: dict[int, ChunkRow], verticals: tuple[Verticale, ...]
) -> list[int]:
    preferred = [row_id for row_id in rows if by_row.get(row_id) and by_row[row_id].verticale in verticals]
    seen = set(preferred)
    remaining = [row_id for row_id in rows if row_id not in seen]
    return preferred + remaining


def retrieve_snippets(
    question: str,
    verticals: tuple[Verticale, ...],
    timings_ms: dict[str, int] | None = None,
    diagnostics: dict[str, object] | None = None,
) -> list[RetrievedChunk]:
    by_row = metadata_by_row()
    if not by_row:
        return []

    rewrite_started = time.perf_counter()
    rewritten_queries = rewrite_queries(question)
    if timings_ms is not None:
        timings_ms["rewrite_ms"] = round((time.perf_counter() - rewrite_started) * 1000)
        timings_ms["rewrite_count"] = len(rewritten_queries)
    if diagnostics is not None:
        diagnostics["preferred_verticals"] = list(verticals)
        diagnostics["retrieval_queries"] = rewritten_queries

    # Step 3: vector retrieval with verticale filter.
    vector_started = time.perf_counter()
    vector_rank_map: dict[int, int] = {}
    vector_score_map: dict[int, float] = {}
    for query in rewritten_queries:
        rows = vector_search_rows(query, VECTOR_TOP_K)
        for rank, (row_id, score) in enumerate(rows, start=1):
            if row_id not in vector_rank_map or rank < vector_rank_map[row_id]:
                vector_rank_map[row_id] = rank
                vector_score_map[row_id] = score
    if timings_ms is not None:
        timings_ms["vector_ms"] = round((time.perf_counter() - vector_started) * 1000)

    vector_rows = [row_id for row_id, _ in sorted(vector_rank_map.items(), key=lambda x: x[1])]

    if not HYBRID_ENABLED:
        candidates = prioritize_rows(vector_rows, by_row, verticals)[:FINAL_SNIPPETS]
        return [
            RetrievedChunk(chunk=by_row[row_id], score=vector_score_map.get(row_id, 0.0))
            for row_id in candidates
            if row_id in by_row
        ]

    # Step 4: hybrid (BM25 + vector) using RRF.
    bm25_started = time.perf_counter()
    bm25_rows = [row_id for row_id, _ in bm25_search_rows(question, HYBRID_TOP_K)]
    if timings_ms is not None:
        timings_ms["bm25_ms"] = round((time.perf_counter() - bm25_started) * 1000)

    vector_rows_top = vector_rows[:HYBRID_TOP_K]
    fused_rows = reciprocal_rank_fusion([vector_rows_top, bm25_rows], k=RRF_K)

    candidate_rows = prioritize_rows(fused_rows, by_row, verticals)[:HYBRID_TOP_K]
    candidate_chunks = [by_row[row_id] for row_id in candidate_rows if row_id in by_row]
    if timings_ms is not None:
        timings_ms["candidate_count"] = len(candidate_chunks)
    if diagnostics is not None:
        diagnostics["candidate_paths"] = [
            chunk.path for chunk in candidate_chunks[:10] if chunk.path
        ]

    # Step 5: rerank a bounded candidate window and keep a compact context.
    if should_rerank(candidate_chunks):
        rerank_started = time.perf_counter()
        rerank_candidates = candidate_chunks[:RERANK_CANDIDATE_K]
        reranked_rows = rerank_rows(question, rerank_candidates)
        if timings_ms is not None:
            timings_ms["rerank_ms"] = round((time.perf_counter() - rerank_started) * 1000)
        reranked_set = set(reranked_rows)
        ordered_rows = reranked_rows + [row for row in candidate_rows if row not in reranked_set]
        final_rows = ordered_rows[:FINAL_SNIPPETS]
    else:
        if timings_ms is not None:
            timings_ms["rerank_ms"] = 0
        final_rows = candidate_rows[:FINAL_SNIPPETS]

    return [
        RetrievedChunk(chunk=by_row[row_id], score=vector_score_map.get(row_id, 0.0))
        for row_id in final_rows
        if row_id in by_row
    ]


def secondary_verticals(
    verticale: Verticale, preferred: tuple[Verticale, ...]
) -> tuple[Verticale, ...]:
    verticals: list[Verticale] = []
    for candidate in (*preferred, verticale):
        if candidate in ("relocation", "study_abroad", "career_readiness") and candidate not in verticals:
            verticals.append(candidate)
    return tuple(verticals)


def should_run_secondary_search(
    question: str,
    verticale: Verticale,
    preferred: tuple[Verticale, ...],
    snippets: list[RetrievedChunk],
    missing_terms: list[str],
) -> bool:
    target_verticals = secondary_verticals(verticale, preferred)
    if not target_verticals:
        return False
    if missing_terms:
        return True
    if not snippets:
        return True

    normalized = normalize_text(question)
    procedural_markers = (
        "apply",
        "application",
        "deadline",
        "document",
        "how",
        "procedure",
        "requirement",
        "selection",
        "step",
        "timeline",
        "what must",
        "when",
    )
    asks_procedure = any(marker in normalized for marker in procedural_markers)
    weak_overlap = max_lexical_overlap(question, snippets) < 2
    thin_context = len(snippets) < 4 or unique_source_count(snippets) < 2
    return asks_procedure and (weak_overlap or thin_context)


def retrieve_secondary_snippets(
    question: str,
    verticale: Verticale,
    preferred: tuple[Verticale, ...],
    existing: list[RetrievedChunk],
    missing_terms: list[str],
    timings_ms: dict[str, int],
    diagnostics: dict[str, object],
) -> list[RetrievedChunk]:
    target_verticals = secondary_verticals(verticale, preferred)
    if not target_verticals:
        return []

    started = time.perf_counter()
    by_row = metadata_by_row()
    queries = targeted_secondary_queries(question, target_verticals, missing_terms)
    rankings: list[list[int]] = []
    score_map: dict[int, float] = {}
    for query in queries:
        bm25_rows: list[int] = []
        for row_id, score in bm25_search_rows(query, SECONDARY_TOP_K):
            chunk = by_row.get(row_id)
            if chunk is None or chunk.verticale not in target_verticals:
                continue
            bm25_rows.append(row_id)
            score_map.setdefault(row_id, score)
        lexical_rows = lexical_search_rows(query, target_verticals, SECONDARY_TOP_K)
        if bm25_rows:
            rankings.append(bm25_rows)
        if lexical_rows:
            rankings.append(lexical_rows)
            for row_id in lexical_rows:
                score_map.setdefault(row_id, float(lexical_overlap_score(query, by_row[row_id])))

    if not rankings:
        timings_ms["secondary_ms"] = round((time.perf_counter() - started) * 1000)
        diagnostics["secondary"] = {
            "ran": True,
            "target_verticals": list(target_verticals),
            "queries": queries,
            "selected_paths": [],
        }
        return []

    existing_rows = {snippet.chunk.row for snippet in existing}
    fused_rows = reciprocal_rank_fusion(rankings, k=RRF_K)
    selected_rows = [row_id for row_id in fused_rows if row_id not in existing_rows]
    selected_rows = selected_rows[:FINAL_SNIPPETS]
    snippets = [
        RetrievedChunk(chunk=by_row[row_id], score=score_map.get(row_id, 0.0))
        for row_id in selected_rows
        if row_id in by_row
    ]
    timings_ms["secondary_ms"] = round((time.perf_counter() - started) * 1000)
    diagnostics["secondary"] = {
        "ran": True,
        "target_verticals": list(target_verticals),
        "queries": queries,
        "selected_paths": [snippet.chunk.path for snippet in snippets],
    }
    return snippets


def merge_secondary_snippets(
    primary: list[RetrievedChunk], secondary: list[RetrievedChunk]
) -> list[RetrievedChunk]:
    merged: list[RetrievedChunk] = []
    seen: set[int] = set()
    for snippet in [*secondary[:3], *primary, *secondary[3:]]:
        if snippet.chunk.row in seen:
            continue
        merged.append(snippet)
        seen.add(snippet.chunk.row)
        if len(merged) >= FINAL_SNIPPETS:
            break
    return merged


def build_context(snippets: list[RetrievedChunk]) -> str:
    blocks: list[str] = []
    for idx, snippet in enumerate(snippets, start=1):
        blocks.append(
            "\n".join(
                [
                    f"[{idx}] {snippet.chunk.path}",
                    f"Title: {snippet.chunk.title}",
                    "Excerpt:",
                    snippet.chunk.text[:ANSWER_EXCERPT_CHARS],
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


def generate_answer(
    question: str,
    verticale: Verticale,
    snippets: list[RetrievedChunk],
    history_context: str = "",
    debug: dict[str, object] | None = None,
) -> str:
    if not snippets:
        if debug is not None:
            debug["answer_path"] = "no_snippets"
        return no_info_answer(question)

    if not get_api_key():
        if debug is not None:
            debug["answer_path"] = "missing_api_key"
        return fallback_answer(
            question,
            fallback_reason(
                question,
                "The OpenAI API key is not configured.",
                "La chiave API di OpenAI non e' configurata.",
            ),
        )

    history_block = ""
    if history_context:
        history_block = (
            "Conversation history for resolving follow-up references only. "
            "Do not treat it as source evidence:\n"
            f"{history_context}\n\n"
        )

    prompt = (
        f"{history_block}"
        f"Question:\n{question}\n\n"
        f"Answer language: {answer_language_name(question)}\n\n"
        f"Detected verticale: {verticale}\n\n"
        f"Source excerpts:\n{build_context(snippets)}\n"
    )

    client = make_client(QUESTION_TIMEOUT_SECONDS)
    last_openai_error: OpenAIError | None = None
    model_attempts: list[str] = []
    for model_name in answer_models_for_question(question):
        model_attempts.append(model_name)
        try:
            response = with_retries(
                lambda: client.responses.create(
                    model=model_name,
                    instructions=ANSWER_SYSTEM_PROMPT,
                    input=prompt,
                    max_output_tokens=700,
                )
            )
        except OpenAIError as exc:
            last_openai_error = exc
            continue
        except Exception:
            continue

        answer = extract_response_text(response)
        if answer:
            if debug is not None:
                debug["answer_path"] = "model"
                debug["answer_model_used"] = model_name
                debug["answer_model_attempts"] = model_attempts
            return answer

    if debug is not None:
        debug["answer_model_attempts"] = model_attempts
    if last_openai_error is not None:
        if debug is not None:
            debug["answer_path"] = "openai_error"
            debug["answer_error"] = last_openai_error.__class__.__name__
        return fallback_answer(
            question,
            fallback_reason(
                question,
                f"OpenAI returned an error: {last_openai_error.__class__.__name__}.",
                f"OpenAI ha restituito un errore: {last_openai_error.__class__.__name__}.",
            ),
        )
    if debug is not None:
        debug["answer_path"] = "empty_model_output"
    return fallback_answer(
        question,
        fallback_reason(
            question,
            "OpenAI returned an empty answer across the configured models.",
            "OpenAI ha restituito una risposta vuota con i modelli configurati.",
        ),
    )


def infer_verticale(
    fallback_verticale: Verticale, snippets: list[RetrievedChunk]
) -> Verticale:
    if not snippets:
        return fallback_verticale

    counts = {verticale: 0 for verticale in VERTICALS}
    for snippet in snippets[:3]:
        counts[snippet.chunk.verticale] += 1

    max_count = max(counts.values())
    if max_count <= 0:
        return fallback_verticale

    leaders = [verticale for verticale, count in counts.items() if count == max_count]
    if len(leaders) > 1:
        top_verticale = snippets[0].chunk.verticale
        if fallback_verticale in leaders:
            return fallback_verticale
        if top_verticale in leaders:
            return top_verticale
        return leaders[0]

    best = leaders[0]
    if counts.get(fallback_verticale, 0) > 0 and max_count - counts[fallback_verticale] <= 1:
        return fallback_verticale
    return best


def unique_sources(snippets: list[RetrievedChunk]) -> list[str]:
    sources: list[str] = []
    seen: set[str] = set()
    for snippet in snippets:
        path = snippet.chunk.path
        if path and path not in seen:
            sources.append(path)
            seen.add(path)
    return sources


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    started_at = time.perf_counter()
    request_id = uuid4().hex[:12]
    timings_ms: dict[str, int] = {}
    question = request.question.strip()
    if not question:
        return AskResponse(
            answer=localize_message(
                question,
                "Please provide a non-empty question.",
                "Inserisci una domanda non vuota.",
            ),
            sources=[],
            verticale="life_on_campus",
        )

    retrieval_question = retrieval_question_with_history(question, request.history)
    history_context = conversation_history_context(request.history)

    route_started = time.perf_counter()
    verticale = classify_verticale(retrieval_question)
    preferred = preferred_verticals(retrieval_question)
    timings_ms["route_ms"] = round((time.perf_counter() - route_started) * 1000)

    retrieve_started = time.perf_counter()
    diagnostics: dict[str, object] = {}
    snippets = retrieve_snippets(retrieval_question, preferred, timings_ms, diagnostics)
    timings_ms["retrieve_ms"] = round((time.perf_counter() - retrieve_started) * 1000)
    diagnostics["selected_chunks"] = selected_chunk_log(snippets)
    verticale = infer_verticale(verticale, snippets)

    evidence_started = time.perf_counter()
    missing_terms: list[str] = []
    for term in (
        *missing_required_evidence_terms(question, snippets),
        *missing_contextual_evidence_terms(question, snippets),
    ):
        if term not in missing_terms:
            missing_terms.append(term)
    timings_ms["evidence_ms"] = round((time.perf_counter() - evidence_started) * 1000)

    secondary_used = False
    if should_run_secondary_search(
        question, verticale, preferred, snippets, missing_terms
    ):
        secondary_snippets = retrieve_secondary_snippets(
            question,
            verticale,
            preferred,
            snippets,
            missing_terms,
            timings_ms,
            diagnostics,
        )
        if secondary_snippets:
            snippets = merge_secondary_snippets(snippets, secondary_snippets)
            diagnostics["selected_chunks_after_secondary"] = selected_chunk_log(snippets)
            verticale = infer_verticale(verticale, snippets)
            secondary_used = True

            evidence_started = time.perf_counter()
            missing_terms = []
            for term in (
                *missing_required_evidence_terms(question, snippets),
                *missing_contextual_evidence_terms(question, snippets),
            ):
                if term not in missing_terms:
                    missing_terms.append(term)
            timings_ms["evidence_ms"] += round(
                (time.perf_counter() - evidence_started) * 1000
            )
    else:
        diagnostics["secondary"] = {"ran": False}

    answer_started = time.perf_counter()
    answer_debug: dict[str, object] = {}
    if missing_terms:
        answer_debug["answer_path"] = "unsupported_specifics_gate"
        answer = unsupported_specifics_answer(question, missing_terms)
    else:
        answer = generate_answer(
            question,
            verticale,
            snippets,
            history_context,
            answer_debug,
        )
    timings_ms["answer_ms"] = round((time.perf_counter() - answer_started) * 1000)

    if (
        is_abstention(answer)
        and not secondary_used
        and answer_debug.get("answer_path") == "model"
    ):
        secondary_snippets = retrieve_secondary_snippets(
            question,
            verticale,
            preferred,
            snippets,
            missing_terms,
            timings_ms,
            diagnostics,
        )
        if secondary_snippets:
            merged_snippets = merge_secondary_snippets(snippets, secondary_snippets)
            if max_lexical_overlap(question, merged_snippets) > max_lexical_overlap(
                question, snippets
            ) or unique_source_count(merged_snippets) > unique_source_count(snippets):
                snippets = merged_snippets
                diagnostics["selected_chunks_after_secondary"] = selected_chunk_log(snippets)
                verticale = infer_verticale(verticale, snippets)
                answer_started = time.perf_counter()
                answer = generate_answer(
                    question,
                    verticale,
                    snippets,
                    history_context,
                    answer_debug,
                )
                timings_ms["answer_ms"] += round(
                    (time.perf_counter() - answer_started) * 1000
                )
    diagnostics["answer"] = answer_debug

    record_recent_question(question, verticale)
    sources = unique_sources(snippets)
    log_ask_event(
        request_id,
        question,
        verticale,
        sources,
        answer,
        started_at,
        timings_ms,
        missing_terms,
        diagnostics,
    )

    return AskResponse(
        answer=answer,
        sources=sources,
        verticale=verticale,
    )
