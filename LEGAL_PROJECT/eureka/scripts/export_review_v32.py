
import json
from pathlib import Path

BASE = Path("data/documents/processed")
STORE = BASE / "structured_legal_document_store_v3.json"
AUDIT = BASE / "clause_audit_v3.json"
OUTPUT = BASE / "review_v32.txt"


def main():
    store = json.loads(STORE.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))

    articles = {
        int(a["article_number"]): a
        for a in store["articles"]
    }

    lines = []

    for result in audit["articles"]:
        if not result["issues"]:
            continue

        number = int(result["article_number"])
        article = articles[number]

        lines.extend([
            "=" * 75,
            f"DIEU {number}",
            f"ISSUES: {result['issues']}",
            f"CLAUSES: {result['clause_numbers']}",
            f"SOURCE: {article.get('source')}",
            "",
            "PARSED STRUCTURE:"
        ])

        for clause in article["clauses"]:
            letters = [
                point["letter"]
                for point in clause["points"]
            ]

            lines.append(
                f"Khoan {clause['number']}: {letters}"
            )

        lines.extend([
            "",
            "ORIGINAL OCR WITH LINE NUMBERS:"
        ])

        text = article.get(
            "body_corrected",
            article["body_raw"]
        )

        for index, line in enumerate(
            text.splitlines(), start=1
        ):
            lines.append(f"{index:03d}: {line}")

        lines.append("")

    OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print("Exported:", OUTPUT)
    print(
        "Articles requiring review:",
        sum(bool(a["issues"]) for a in audit["articles"])
    )


if __name__ == "__main__":
    main()
