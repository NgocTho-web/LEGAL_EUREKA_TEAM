
import json
import re
from pathlib import Path
from collections import defaultdict

BASE = Path("data/documents/processed")

STORE = BASE / "structured_legal_document_store_v3.json"
AUDIT = BASE / "content_preservation_audit_v1.json"
OUTPUT = BASE / "content_preservation_review_v2.txt"


def normalize(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


store = json.loads(STORE.read_text(encoding="utf-8"))
audit = json.loads(AUDIT.read_text(encoding="utf-8"))

articles = {
    int(a["article_number"]): a
    for a in store["articles"]
}

grouped = defaultdict(list)

for issue in audit["issues"]:
    grouped[int(issue["article"])].append(issue)

lines = [
    "CONTENT PRESERVATION REVIEW V2",
    "=" * 80,
    f"Articles requiring review: {len(grouped)}",
    ""
]

for number in sorted(grouped):
    article = articles[number]
    body = article.get("body_corrected") or article["body_raw"]

    lines.extend([
        "=" * 80,
        f"DIEU {number}",
        "=" * 80,
        "",
        "ISSUES:"
    ])

    for issue in grouped[number]:
        lines.append(
            f"  {issue['type']}: {issue['detail']}"
        )

    lines.extend(["", "OCR BODY:"])

    for index, text in enumerate(body.splitlines(), 1):
        lines.append(f"{index:03d}: {text}")

    lines.extend(["", "PARSED SEGMENTS:"])

    preamble = article.get("preamble")
    if normalize(preamble):
        lines.append(f"\nPREAMBLE:\n{preamble}")

    for clause in article.get("clauses", []):
        lines.append(
            f"\nKHOAN {clause['number']} "
            f"(start_line={clause.get('start_line')}):"
        )

        lines.append(str(clause.get("text", "")))

        for point in clause.get("points", []):
            lines.append(
                f"\n  DIEM {point['letter']} "
                f"(start_line={point.get('start_line')}):"
            )
            lines.append(str(point.get("text", "")))

    lines.append("\n")

OUTPUT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("CONTENT PRESERVATION REVIEW V2")
print("=" * 60)
print("Articles requiring review:", len(grouped))
print("Issues:", len(audit["issues"]))
print("Saved:", OUTPUT)
