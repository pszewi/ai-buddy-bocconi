"""Build chunk and vector index artifacts for the Bocconi AI Buddy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import BadRequestError, OpenAI

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
INDEX_DIR = DATA_DIR / "index"
MANIFEST_PATH = DATA_DIR / "manifest.json"
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
FAISS_PATH = INDEX_DIR / "faiss.bin"
META_PATH = INDEX_DIR / "metadata.jsonl"
VERTICALS = {"relocation", "life_on_campus", "study_abroad", "career_readiness"}

WORD_RE = re.compile(r"\S+")
DATA_URI_RE = re.compile(r"data:image/[^\s)]+", re.IGNORECASE)
LONG_URL_RE = re.compile(r"https?://\S{180,}", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build chunk and vector index artifacts.")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--chunk-only", action="store_true")
    return parser.parse_args()


def strip_frontmatter(raw: str) -> str:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return raw.strip()


def parse_frontmatter(raw: str) -> dict[str, str]:
    if not raw.startswith("---"):
        return {}

    parts = raw.split("---", 2)
    if len(parts) != 3:
        return {}

    fields: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("'\"")
    return fields


def chunk_words(words: list[str], chunk_size: int, overlap: int) -> Iterable[tuple[int, int]]:
    step = max(1, chunk_size - overlap)
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        yield start, end
        if end >= len(words):
            break
        start += step


def sanitize_text(text: str) -> str:
    text = DATA_URI_RE.sub(" ", text)
    text = LONG_URL_RE.sub(" ", text)
    words = []
    for token in WORD_RE.findall(text):
        if len(token) > 120:
            continue
        words.append(token)
    return " ".join(words)


def load_manifest() -> dict:
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_chunks(chunk_size: int, overlap: int) -> list[dict]:
    manifest = load_manifest()
    manifest_files = {
        item.get("path")
        for item in manifest.get("files", [])
        if item.get("path")
    }
    files = list(manifest.get("files", []))
    for verticale in sorted(VERTICALS):
        for file_path in sorted((DATA_DIR / verticale).glob("*.md")):
            relative_path = file_path.relative_to(DATA_DIR).as_posix()
            if relative_path in manifest_files:
                continue
            try:
                raw = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            frontmatter = parse_frontmatter(raw)
            files.append(
                {
                    "path": relative_path,
                    "verticale": frontmatter.get("verticale", verticale),
                    "language": frontmatter.get("language", "en"),
                    "title": frontmatter.get("title", relative_path),
                }
            )

    chunks: list[dict] = []
    for item in files:
        relative_path = item.get("path")
        if not relative_path:
            continue
        file_path = DATA_DIR / relative_path
        try:
            raw = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        body = sanitize_text(strip_frontmatter(raw))
        words = WORD_RE.findall(body)
        if not words:
            continue

        title = item.get("title") or relative_path
        verticale = item.get("verticale") or "life_on_campus"
        for chunk_idx, (start, end) in enumerate(chunk_words(words, chunk_size, overlap)):
            chunk_text = " ".join(words[start:end]).strip()
            if not chunk_text:
                continue

            id_seed = f"{relative_path}:{chunk_idx}:{start}:{end}"
            chunk_id = hashlib.sha1(id_seed.encode("utf-8")).hexdigest()[:16]
            chunks.append(
                {
                    "id": chunk_id,
                    "path": relative_path,
                    "verticale": verticale,
                    "title": title,
                    "text": chunk_text,
                }
            )
    return chunks


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def embed_chunks(chunks: list[dict], batch_size: int) -> np.ndarray:
    client = OpenAI()
    vectors: list[list[float]] = []
    for idx in range(0, len(chunks), batch_size):
        batch = chunks[idx : idx + batch_size]
        texts = [chunk["text"] for chunk in batch]
        try:
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=texts,
            )
            vectors.extend([item.embedding for item in response.data])
            continue
        except BadRequestError as exc:
            message = str(exc).lower()
            if "maximum input length" not in message:
                raise

        # Fallback: embed one by one with conservative truncation.
        for text in texts:
            safe_text = text[:10000]
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=safe_text,
            )
            vectors.append(response.data[0].embedding)
    matrix = np.array(vectors, dtype="float32")
    faiss.normalize_L2(matrix)
    return matrix


def persist_faiss(vectors: np.ndarray, chunks: list[dict]) -> None:
    if vectors.ndim != 2 or vectors.shape[0] == 0:
        raise ValueError("No vectors to persist.")
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    faiss.write_index(index, str(FAISS_PATH))

    metadata_rows: list[dict] = []
    for row_idx, chunk in enumerate(chunks):
        metadata_rows.append(
            {
                "row": row_idx,
                "id": chunk["id"],
                "path": chunk["path"],
                "verticale": chunk["verticale"],
                "title": chunk["title"],
                "text": chunk["text"],
            }
        )
    write_jsonl(META_PATH, metadata_rows)


def main() -> None:
    args = parse_args()
    load_dotenv(BACKEND_DIR / ".env")

    chunks = build_chunks(args.chunk_size, args.overlap)
    write_jsonl(CHUNKS_PATH, chunks)
    print(f"chunk_count={len(chunks)}")
    print(f"chunks_path={CHUNKS_PATH}")

    if args.chunk_only:
        return

    chunks_for_index = read_jsonl(CHUNKS_PATH)
    vectors = embed_chunks(chunks_for_index, args.batch_size)
    persist_faiss(vectors, chunks_for_index)
    print(f"vector_rows={vectors.shape[0]}")
    print(f"vector_dim={vectors.shape[1]}")
    print(f"faiss_path={FAISS_PATH}")
    print(f"metadata_path={META_PATH}")


if __name__ == "__main__":
    main()
