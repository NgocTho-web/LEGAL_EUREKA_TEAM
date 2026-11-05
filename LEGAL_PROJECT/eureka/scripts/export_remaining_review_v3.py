
import json
from pathlib import Path

BASE = Path("data/documents/processed")

STORE_PATH = BASE / "structured_legal_document_store_v3.json"
AUDIT_PATH = BASE / "clause_audit_v3.json"
OUTPUT_PATH = BASE / "remaining_review_v3.txt"


def main():
    with STORE_PATH.open(encoding="utf-8") as f:
        store = json.load(f)

    with AUDIT_PATH.open(encoding="utf-8") as f:
        audit = json.load(f)

    articles = {
        int(a["article_number"]): a
        for a in store["articles"]
    }

    output = []

    for result in audit["articles"]:
        if not result["issues"]:
            continue

        number = int(result["article_number"])
        article = articles[number]

        output.append("=" * 75)
        output.append(f"DIEU {number}")
        output.append("=" * 75)
        output.append(
            f"PDF source: {article.get('source', {})}"
        )
        output.append(
            f"Khoan: {result['clause_numbers']}"
        )
        output.append(
            f"Issues: {result['issues']}"
        )

        for clause in article["clauses"]:
            letters = [
                p["letter"]
                for p in clause["points"]
            ]

            output.append(
                f"  Khoan {clause['number']}: "
                f"points={letters}"
            )

        output.append("\nOCR LINES:")

        for index, line in enumerate(
            article["body_corrected"].splitlines(),
            start=1
        ):
            output.append(f"{index:03d}: {line}")

        output.append("")

    OUTPUT_PATH.write_text(
        "\n".join(output),
        encoding="utf-8"
    )

    print("Exported:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
