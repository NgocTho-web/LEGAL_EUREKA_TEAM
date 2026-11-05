
import json
import re
from pathlib import Path

STORE_PATH = Path(
    "data/documents/processed/legal_document_store.json"
)

OUTPUT_PATH = Path(
    "data/documents/processed/clause_audit_v2.json"
)

# Cho phép một số ký tự OCR nhiễu trước số Khoản.
CLAUSE_RE = re.compile(
    r"^\s*[|[\]:,;!Ịìĩ]*\s*"
    r"(\d{1,2})\s*[.,]\s+(.+)$"
)

POINT_RE = re.compile(
    r"^\s*[|[\]:;!]*\s*"
    r"([a-zđ])\s*[)]\s*(.+)$",
    re.IGNORECASE
)

# Dòng giống số thứ tự nhưng chưa chắc là Khoản.
SUSPICIOUS_NUMBER_RE = re.compile(
    r"^\s*[|[\]:,;!Ịìĩ]*\s*"
    r"(\d{1,2})\s*[.,)]"
)


def parse_article(article):
    clauses = []
    suspicious_lines = []

    current_clause = None
    current_point = None

    for line_no, raw_line in enumerate(
        article["body_raw"].splitlines(), 1
    ):
        line = raw_line.strip()

        if not line:
            continue

        clause_match = CLAUSE_RE.match(line)
        point_match = POINT_RE.match(line)

        if clause_match:
            number = int(clause_match.group(1))
            content = clause_match.group(2).strip()

            # Không tự nhận số quá lớn là Khoản.
            # Giới hạn này là heuristic, cần kiểm định.
            if number > 30:
                suspicious_lines.append({
                    "line": line_no,
                    "raw": raw_line,
                    "reason": "large_clause_number"
                })
                continue

            current_clause = {
                "clause_number": number,
                "start_line": line_no,
                "text_lines": [content],
                "points": []
            }

            clauses.append(current_clause)
            current_point = None
            continue

        if point_match and current_clause:
            current_point = {
                "point_label": point_match.group(1).lower(),
                "start_line": line_no,
                "text_lines": [
                    point_match.group(2).strip()
                ]
            }

            current_clause["points"].append(
                current_point
            )
            continue

        if SUSPICIOUS_NUMBER_RE.match(line):
            suspicious_lines.append({
                "line": line_no,
                "raw": raw_line,
                "reason": "unparsed_numbered_line"
            })

        # Giữ nguyên dòng chưa nhận diện,
        # không xóa khỏi nội dung phân tích.
        if current_point is not None:
            current_point["text_lines"].append(line)
        elif current_clause is not None:
            current_clause["text_lines"].append(line)

    for clause in clauses:
        clause["text"] = " ".join(
            clause.pop("text_lines")
        )

        for point in clause["points"]:
            point["text"] = " ".join(
                point.pop("text_lines")
            )

    return {
        "clauses": clauses,
        "suspicious_lines": suspicious_lines
    }


def audit_article(article):
    result = parse_article(article)
    clauses = result["clauses"]

    numbers = [
        c["clause_number"] for c in clauses
    ]

    issues = []

    if numbers and numbers != list(
        range(1, len(numbers) + 1)
    ):
        issues.append("non_sequential_clauses")

    if len(numbers) != len(set(numbers)):
        issues.append("duplicate_clauses")

    for clause in clauses:
        labels = [
            p["point_label"]
            for p in clause["points"]
        ]

        if len(labels) != len(set(labels)):
            issues.append(
                f"duplicate_points_clause_"
                f"{clause['clause_number']}"
            )

        if labels:
            expected = [
                chr(ord("a") + i)
                for i in range(len(labels))
            ]

            if labels != expected:
                issues.append(
                    f"non_sequential_points_clause_"
                    f"{clause['clause_number']}"
                )

    return {
        "article_number": article["article_number"],
        "clause_count": len(clauses),
        "point_count": sum(
            len(c["points"]) for c in clauses
        ),
        "clause_numbers": numbers,
        "issues": issues,
        "suspicious_lines": result["suspicious_lines"]
    }


def main():
    with STORE_PATH.open(
        "r", encoding="utf-8"
    ) as f:
        store = json.load(f)

    reports = [
        audit_article(article)
        for article in store["articles"]
    ]

    summary = {
        "article_count": len(reports),
        "total_clauses": sum(
            r["clause_count"] for r in reports
        ),
        "total_points": sum(
            r["point_count"] for r in reports
        ),
        "articles_with_issues": sum(
            bool(r["issues"]) for r in reports
        ),
        "articles_with_suspicious_lines": sum(
            bool(r["suspicious_lines"])
            for r in reports
        )
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True, exist_ok=True
    )

    with OUTPUT_PATH.open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "summary": summary,
                "articles": reports
            },
            f,
            ensure_ascii=False,
            indent=2
        )

    print("=" * 60)
    print("CLAUSE PARSER V2 AUDIT")
    print("=" * 60)

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nChi tiet cac dieu uu tien:")

    for number in [3, 102, 136, 141, 188, 204]:
        item = next(
            r for r in reports
            if r["article_number"] == number
        )

        print(f"\nDieu {number}")
        print("Khoan:", item["clause_numbers"])
        print("Diem:", item["point_count"])
        print("Issues:", item["issues"])
        print(
            "Suspicious:",
            item["suspicious_lines"]
        )

    print("\nSaved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
