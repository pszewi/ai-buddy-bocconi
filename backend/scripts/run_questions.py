"""Run a JSONL question set against /ask and save JSONL plus Markdown output."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run evaluation questions.")
    parser.add_argument(
        "--questions",
        default="/app/eval/extended_questions.jsonl",
        help="Input JSONL with at least id and question fields.",
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/ask",
        help="Full /ask URL.",
    )
    parser.add_argument(
        "--output",
        default="/app/eval/results/extended-results.jsonl",
        help="Output JSONL file path.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional number of questions to run.",
    )
    parser.add_argument(
        "--ids",
        default="",
        help="Optional comma-separated IDs to run, e.g. R01,L03,C05.",
    )
    return parser.parse_args()


def load_questions(path: Path) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not row.get("id") or not row.get("question"):
                raise ValueError(f"{path}:{line_number} must include id and question")
            questions.append(row)
    return questions


def call_ask(url: str, question: str, timeout: float) -> dict[str, Any]:
    payload = json.dumps({"question": question}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
            status: int | str = response.status
    except urllib.error.URLError as exc:
        return {
            "status": "error",
            "latency_s": round(time.perf_counter() - start, 3),
            "error": str(exc),
        }

    return {
        "status": status,
        "latency_s": round(time.perf_counter() - start, 3),
        "verticale": parsed.get("verticale"),
        "answer": parsed.get("answer", ""),
        "sources": parsed.get("sources", []),
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    md_path = path.with_suffix(".md")
    with md_path.open("w", encoding="utf-8") as handle:
        handle.write("# Extended Evaluation Results\n\n")
        for row in rows:
            handle.write(f"## {row['id']}\n")
            handle.write(f"Question: {row['question']}\n")
            handle.write(f"Expected verticale: {row.get('expected_verticale')}\n")
            handle.write(f"Returned verticale: {row.get('verticale')}\n")
            handle.write(f"Category: {row.get('category')}\n")
            handle.write(f"Latency: {row.get('latency_s')}s\n")
            handle.write(f"Status: {row.get('status')}\n\n")
            handle.write("Expected facts:\n")
            handle.write(f"{row.get('expected', '')}\n\n")
            handle.write("Answer:\n")
            handle.write(f"{row.get('answer', row.get('error', ''))}\n\n")
            handle.write("Expected sources:\n")
            for source in row.get("expected_sources", []):
                handle.write(f"- {source}\n")
            handle.write("\nReturned sources:\n")
            for source in row.get("sources", []):
                handle.write(f"- {source}\n")
            handle.write("\n")


def main() -> None:
    args = parse_args()
    questions = load_questions(Path(args.questions))
    selected_ids = {item.strip() for item in args.ids.split(",") if item.strip()}
    if selected_ids:
        questions = [row for row in questions if row["id"] in selected_ids]
    if args.limit > 0:
        questions = questions[: args.limit]

    rows: list[dict[str, Any]] = []
    for item in questions:
        result = call_ask(args.url, item["question"], args.timeout)
        rows.append(
            {
                "id": item["id"],
                "question": item["question"],
                "category": item.get("category"),
                "expected_verticale": item.get("verticale"),
                "expected": item.get("expected", ""),
                "expected_sources": item.get("sources", []),
                **result,
            }
        )
        print(
            f"{item['id']} {rows[-1]['latency_s']}s "
            f"status={rows[-1]['status']} v={rows[-1].get('verticale')} "
            f"src={len(rows[-1].get('sources', []))}"
        )

    output_path = Path(args.output)
    write_jsonl(output_path, rows)
    write_markdown(output_path, rows)
    print(output_path)
    print(output_path.with_suffix(".md"))


if __name__ == "__main__":
    main()
