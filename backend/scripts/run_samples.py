"""Run SAMPLE_QUESTIONS.md against /ask and log answers, sources, latency."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

QUESTIONS = [
    "What is the price of an annual ATM transit pass for students under 27 in Milan, and how does it compare with the standard adult annual urban pass?",
    "List the steps an international student must follow to register with Italy's National Health Service (SSN) in Milan.",
    "Confrontando i bus diretti da Malpensa a Milano Centrale tra i vettori documentati (Autostradale/Malpensa Bus Express, Terravision, Flibco, FlixBus): qual e' il prezzo di partenza piu' basso indicato per ciascun vettore?",
    "Quale documento devo portare per accedere alla Biblioteca Bocconi, e qual e' la capienza massima dell'edificio?",
    "Provide a structured table of the dining areas available on the Bocconi campus, indicating the location of each and its meal/opening pattern.",
    "For the Bocconi MSc graduate Exchange Program selection score, how are academic GPA, credits, and Bachelor degree grade weighted? Show the weights and explain.",
    "What is the application deadline for the Bocconi Double Degree program with MIT (Massachusetts Institute of Technology)?",
    "What is the maximum amount of the Bocconi Merit Award tuition waiver for graduate (Master of Science) students, and what is the format of the award (e.g. tuition waiver only, tuition waiver plus stipend, etc.)?",
    "What are the placement results published in the 2026 BESS graduate survey?",
    "How many different paid Bocconi Sport Membership tiers are listed for the 2025/2026 season, and which is the cheapest one available to UB and SDA Bocconi students?",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the 10 sample questions.")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/ask",
        help="Full /ask URL.",
    )
    parser.add_argument(
        "--output",
        default="/tmp/buddy_samples.jsonl",
        help="Output JSONL file path.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds.",
    )
    return parser.parse_args()


def call_ask(url: str, question: str, timeout: float) -> dict:
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
            status = response.status
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


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for idx, question in enumerate(QUESTIONS, start=1):
        result = call_ask(args.url, question, args.timeout)
        rows.append(
            {
                "n": idx,
                "question": question,
                **result,
            }
        )

    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(output_path)
    for row in rows:
        source_count = len(row.get("sources", []))
        print(
            f"Q{row['n']:02d} {row['latency_s']}s "
            f"status={row['status']} v={row.get('verticale')} src={source_count}"
        )


if __name__ == "__main__":
    main()
