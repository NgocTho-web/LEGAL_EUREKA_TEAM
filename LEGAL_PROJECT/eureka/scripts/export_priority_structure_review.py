
import json
from pathlib import Path

BASE = Path("data/documents/processed")
INPUT = BASE / "structured_legal_document_store_v3.json"
OUTPUT = BASE / "priority_structure_review.txt"

PRIORITY = [21, 34, 179, 183, 201, 209]

data = json.loads(INPUT.read_text(encoding="utf-8"))
articles = {
    int(a["article_number"]): a
    for a in data["articles"]
}

lines = ["PRIORITY STRUCTURE REVIEW", "=" * 80]

for number in PRIORITY:
    article = articles[number]
    body = article.get("body_corrected") or article["body_raw"]

    lines.extend([
        "",
        "=" * 80,
        f"DIEU {number}",
        "=" * 80,
        f"Source: {article.get('source')}",
        "",
        "OCR BODY:"
    ])

    for i, line in enumerate(body.splitlines(), 1):
        lines.append(f"{i:03d}: {line}")

    lines.extend(["", "PARSED STRUCTURE:"])

    preamble = article.get("preamble", "")
    if preamble:
        lines.append(f"PREAMBLE:\n{preamble}")

    for clause in article.get("clauses", []):
        lines.append(
            f"\nKHOAN {clause['number']} "
            f"(line {clause.get('start_line')}):"
        )
        lines.append(clause.get("text", ""))

        for point in clause.get("points", []):
            lines.append(
                f"\n  DIEM {point['letter']} "
                f"(line {point.get('start_line')}):"
            )
            lines.append(point.get("text", ""))

OUTPUT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("Exported:", OUTPUT)
print("Articles:", PRIORITY)
