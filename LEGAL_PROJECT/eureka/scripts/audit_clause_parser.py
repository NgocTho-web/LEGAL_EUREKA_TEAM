
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_clause_parser import parse_article

STORE_PATH = Path(
    "data/documents/processed/legal_document_store.json"
)

OUTPUT_PATH = Path(
    "data/documents/processed/clause_audit.json"
)


def main():
    with STORE_PATH.open("r", encoding="utf-8") as f:
        store = json.load(f)

    reports = []
    total_clauses = 0
    total_points = 0

    for article in store["articles"]:
        number = article["article_number"]
        clauses = parse_article(article)

        clause_numbers = [
            clause["clause_number"]
            for clause in clauses
        ]

        issues = []

        if not clauses:
            issues.append("no_clauses_detected")

        duplicates = [
            n for n, count in Counter(clause_numbers).items()
            if count > 1
        ]

        if duplicates:
            issues.append(
                f"duplicate_clauses:{duplicates}"
            )

        if clause_numbers and clause_numbers != list(
            range(1, len(clause_numbers) + 1)
        ):
            issues.append("non_sequential_clauses")

        for clause in clauses:
            labels = [
                p["point_label"].lower()
                for p in clause["points"]
            ]

            if len(labels) != len(set(labels)):
                issues.append(
                    f"duplicate_points_in_clause_"
                    f"{clause['clause_number']}"
                )

            if labels:
                expected = [
                    chr(ord("a") + i)
                    for i in range(len(labels))
                ]

                if labels != expected:
                    issues.append(
                        f"non_sequential_points_in_clause_"
                        f"{clause['clause_number']}"
                    )

        point_count = sum(
            len(c["points"]) for c in clauses
        )

        total_clauses += len(clauses)
        total_points += point_count

        reports.append({
            "article_number": number,
            "clause_count": len(clauses),
            "point_count": point_count,
            "clause_numbers": clause_numbers,
            "issues": issues
        })

    review_articles = [
        r for r in reports if r["issues"]
    ]

    report = {
        "document_id": store["document_id"],
        "article_count": len(reports),
        "total_detected_clauses": total_clauses,
        "total_detected_points": total_points,
        "articles_needing_review": len(review_articles),
        "review_articles": review_articles,
        "articles": reports,
        "status": "structural_audit_only"
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            report, f, ensure_ascii=False, indent=2
        )

    print("=" * 60)
    print("CLAUSE & POINT AUDIT")
    print("=" * 60)
    print("So dieu:", len(reports))
    print("So khoan nhan dien:", total_clauses)
    print("So diem nhan dien:", total_points)
    print("So dieu can kiem tra:", len(review_articles))
    print("\nDanh sach dieu can kiem tra:")

    for item in review_articles:
        print(
            f"Dieu {item['article_number']}: "
            f"{', '.join(item['issues'])}"
        )

    print("\nBao cao:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
