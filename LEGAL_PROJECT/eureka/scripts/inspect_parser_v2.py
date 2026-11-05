
import json
from pathlib import Path

STORE = Path(
    "data/documents/processed/legal_document_store.json"
)

AUDIT = Path(
    "data/documents/processed/clause_audit_v2.json"
)

OUTPUT = Path(
    "data/documents/processed/parser_v2_review.txt"
)

PRIORITY = [3, 10, 102, 136, 141, 188, 204]


def main():
    with STORE.open(encoding="utf-8") as f:
        store = json.load(f)

    with AUDIT.open(encoding="utf-8") as f:
        audit = json.load(f)

    articles = {
        a["article_number"]: a
        for a in store["articles"]
    }

    reports = {
        a["article_number"]: a
        for a in audit["articles"]
    }

    output = []

    for number in PRIORITY:
        article = articles[number]
        report = reports[number]

        output.append("=" * 70)
        output.append(f"DIEU {number}")
        output.append("=" * 70)

        output.append(
            f"Khoan: {report['clause_numbers']}"
        )
        output.append(
            f"Canh bao: {report['issues']}"
        )

        lines = article["body_raw"].splitlines()

        suspicious = {
            item["line"]
            for item in report["suspicious_lines"]
        }

        for i, line in enumerate(lines, 1):
            marker = " >>>" if i in suspicious else "    "
            output.append(
                f"{marker} {i:03d}: {line}"
            )

        output.append("")

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT.write_text(
        "\n".join(output),
        encoding="utf-8"
    )

    print("Da tao:", OUTPUT)


if __name__ == "__main__":
    main()
