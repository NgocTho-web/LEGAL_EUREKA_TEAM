
import json
from pathlib import Path
from collections import Counter

BASE = Path("data/documents/processed")

SOURCE = BASE / "legal_document_store.json"
STRUCTURED = BASE / "structured_legal_document_store_v3.json"
CORRECTIONS = BASE / "verified_ocr_corrections.json"
AUDIT = BASE / "clause_audit_v3.json"

REPORT = BASE / "legal_store_integrity_report.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    original = load(SOURCE)
    structured = load(STRUCTURED)
    corrections = load(CORRECTIONS)["corrections"]
    audit = load(AUDIT)

    errors = []
    warnings = []

    original_articles = {
        int(a["article_number"]): a
        for a in original["articles"]
    }

    structured_articles = structured["articles"]
    numbers = [
        int(a["article_number"])
        for a in structured_articles
    ]

    if len(numbers) != 212:
        errors.append(
            f"Expected 212 articles, found {len(numbers)}"
        )

    duplicates = [
        number for number, count
        in Counter(numbers).items()
        if count > 1
    ]

    if duplicates:
        errors.append(
            f"Duplicate articles: {duplicates}"
        )

    missing = sorted(set(range(1, 213)) - set(numbers))

    if missing:
        errors.append(f"Missing articles: {missing}")

    rules_by_article = {}

    for rule in corrections:
        number = int(rule["article"])
        rules_by_article.setdefault(number, []).append(rule)

    for article in structured_articles:
        number = int(article["article_number"])

        if number not in original_articles:
            errors.append(f"Unknown article: {number}")
            continue

        raw = original_articles[number]["body_raw"]
        expected = raw

        for rule in rules_by_article.get(number, []):
            old = rule["find"]
            new = rule["replace"]

            if expected.count(old) != 1:
                errors.append(
                    f"Article {number}: correction mismatch"
                )
                continue

            expected = expected.replace(old, new, 1)

        actual = article.get("body_corrected")

        if actual != expected:
            errors.append(
                f"Article {number}: corrected OCR mismatch"
            )

        clauses = article.get("clauses", [])

        clause_numbers = [
            int(c["number"]) for c in clauses
        ]

        if len(clause_numbers) != len(set(clause_numbers)):
            errors.append(
                f"Article {number}: duplicate clause number"
            )

        for clause in clauses:
            letters = [
                str(p["letter"])
                for p in clause.get("points", [])
            ]

            if len(letters) != len(set(letters)):
                errors.append(
                    f"Article {number}, clause "
                    f"{clause['number']}: duplicate point"
                )

        if not article.get("source"):
            warnings.append(
                f"Article {number}: missing PDF source"
            )

        if not article.get("verification_status"):
            warnings.append(
                f"Article {number}: missing verification status"
            )

    remaining_issues = [
        a for a in audit["articles"]
        if a.get("issues")
    ]

    if remaining_issues:
        errors.append(
            f"{len(remaining_issues)} articles have audit issues"
        )

    report = {
        "article_count": len(numbers),
        "correction_count": len(corrections),
        "audit_issue_articles": len(remaining_issues),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL"
    }

    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 60)
    print("LEGAL DOCUMENT STORE INTEGRITY CHECK")
    print("=" * 60)
    print("Articles:", len(numbers))
    print("Corrections:", len(corrections))
    print("Audit issue articles:", len(remaining_issues))
    print("Errors:", len(errors))
    print("Warnings:", len(warnings))
    print("Status:", report["status"])
    print("Report:", REPORT)

    for message in errors[:20]:
        print("ERROR:", message)

    for message in warnings[:20]:
        print("WARNING:", message)

    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
