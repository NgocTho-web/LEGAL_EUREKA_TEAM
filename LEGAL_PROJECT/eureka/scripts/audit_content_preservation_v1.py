
import json
import re
from pathlib import Path

BASE = Path("data/documents/processed")
INPUT = BASE / "structured_legal_document_store_v3.json"
OUTPUT = BASE / "content_preservation_audit_v1.json"
REVIEW = BASE / "content_preservation_review_v1.txt"

data = json.loads(INPUT.read_text(encoding="utf-8"))

issues = []
stats = {
    "articles": 0,
    "clauses": 0,
    "points": 0,
    "missing_segments": 0,
    "out_of_order_segments": 0,
    "suspicious_ocr_lines": 0,
}


def normalize(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def add_issue(article, kind, detail):
    issues.append({
        "article": article,
        "type": kind,
        "detail": detail,
    })


for article in data["articles"]:
    number = int(article["article_number"])
    stats["articles"] += 1

    body = article.get("body_corrected") or article.get("body_raw", "")
    normalized_body = normalize(body)

    segments = []

    preamble = normalize(article.get("preamble"))
    if preamble:
        segments.append(("preamble", preamble))

    for clause in article.get("clauses", []):
        clause_number = clause["number"]
        stats["clauses"] += 1

        clause_text = normalize(clause.get("text"))
        if clause_text:
            segments.append((
                f"clause_{clause_number}",
                clause_text
            ))

        for point in clause.get("points", []):
            stats["points"] += 1

            point_text = normalize(point.get("text"))
            if point_text:
                segments.append((
                    f"clause_{clause_number}_point_{point['letter']}",
                    point_text
                ))

    cursor = 0

    for label, segment in segments:
        position = normalized_body.find(segment)

        if position < 0:
            stats["missing_segments"] += 1
            add_issue(
                number,
                "segment_not_found",
                label
            )
            continue

        if position < cursor:
            stats["out_of_order_segments"] += 1
            add_issue(
                number,
                "segment_out_of_order",
                label
            )

        cursor = max(cursor, position + len(segment))

    for line_number, line in enumerate(body.splitlines(), 1):
        stripped = line.strip()

        if not stripped:
            continue

        suspicious = (
            bool(re.fullmatch(r"\d{1,3}", stripped))
            or bool(re.fullmatch(r"[|¡ỊLNh_.\s]{1,8}", stripped))
            or bool(re.search(r"\bn\d{2,3}\b", stripped))
        )

        if suspicious:
            stats["suspicious_ocr_lines"] += 1
            add_issue(
                number,
                "suspicious_ocr_line",
                f"line {line_number}: {stripped}"
            )


report = {
    "statistics": stats,
    "issues": issues,
    "status": "REVIEW_REQUIRED" if issues else "PASS"
}

OUTPUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

lines = [
    "CONTENT PRESERVATION AUDIT V1",
    "=" * 70,
    "",
    *[f"{key}: {value}" for key, value in stats.items()],
    "",
    "ISSUES",
    "=" * 70,
]

for issue in issues:
    lines.append(
        f"Dieu {issue['article']} | "
        f"{issue['type']} | "
        f"{issue['detail']}"
    )

REVIEW.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("=" * 60)
print("CONTENT PRESERVATION AUDIT V1")
print("=" * 60)

for key, value in stats.items():
    print(f"{key}: {value}")

print("Status:", report["status"])
print("JSON:", OUTPUT)
print("Review:", REVIEW)
