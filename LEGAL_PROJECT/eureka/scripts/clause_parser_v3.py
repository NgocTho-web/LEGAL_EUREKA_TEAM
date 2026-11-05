
import json
import re
from pathlib import Path
from collections import Counter

BASE = Path("data/documents/processed")

STORE_PATH = BASE / "legal_document_store.json"
CORRECTIONS_PATH = BASE / "verified_ocr_corrections.json"

OUTPUT_PATH = BASE / "structured_legal_document_store_v3.json"
AUDIT_PATH = BASE / "clause_audit_v3.json"

CLAUSE_RE = re.compile(
    r"^\s*[|:;,\[\]!¡Ịìĩ]*\s*(\d{1,2})\s*[.,]\s+(.+)$"
)

POINT_RE = re.compile(
    r"^\s*[|:;,\[\]!¡Ịìĩ]*\s*([a-zđ])\s*\)\s*(.+)$",
    re.IGNORECASE
)

NOISE_RE = re.compile(
    r"^\s*(?:\d{1,3}|[|&°.\s]+)\s*$"
)

POINT_ORDER = list("abcdđeghiklmnopqrstuvxy")


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def apply_corrections(article, rules):
    text = article["body_raw"]

    for rule in rules:
        if rule["article"] != article["article_number"]:
            continue

        old = rule["find"]
        new = rule["replace"]

        if text.count(old) != 1:
            raise ValueError(
                f"Correction mismatch: Dieu "
                f"{article['article_number']}: {old}"
            )

        text = text.replace(old, new, 1)

    return text


def parse_article(text):
    clauses = []
    preamble = []
    current_clause = None
    current_point = None
    ignored_noise = []

    def flush_point():
        nonlocal current_point

        if current_point is not None:
            current_point["text"] = "\n".join(
                current_point.pop("lines")
            ).strip()

            current_clause["points"].append(
                current_point
            )
            current_point = None

    def flush_clause():
        nonlocal current_clause

        if current_clause is not None:
            flush_point()

            current_clause["text"] = "\n".join(
                current_clause.pop("lines")
            ).strip()

            clauses.append(current_clause)
            current_clause = None

    for line_number, raw_line in enumerate(
        text.splitlines(), start=1
    ):
        line = raw_line.strip()

        if not line:
            continue

        clause_match = CLAUSE_RE.match(line)

        if clause_match:
            number = int(clause_match.group(1))

            if 1 <= number <= 30:
                flush_clause()

                current_clause = {
                    "number": number,
                    "start_line": line_number,
                    "lines": [clause_match.group(2)],
                    "points": []
                }
                continue

        point_match = POINT_RE.match(line)

        if point_match and current_clause is not None:
            flush_point()

            current_point = {
                "letter": point_match.group(1).lower(),
                "start_line": line_number,
                "lines": [point_match.group(2)]
            }
            continue

        if NOISE_RE.match(line):
            ignored_noise.append({
                "line": line_number,
                "text": raw_line
            })
            continue

        if current_point is not None:
            current_point["lines"].append(raw_line)

        elif current_clause is not None:
            current_clause["lines"].append(raw_line)

        else:
            preamble.append(raw_line)

    flush_clause()

    return {
        "preamble": "\n".join(preamble).strip(),
        "clauses": clauses,
        "ignored_noise": ignored_noise
    }


def audit_article(parsed):
    issues = []

    numbers = [
        c["number"] for c in parsed["clauses"]
    ]

    if numbers:
        expected = list(range(1, max(numbers) + 1))

        if numbers != expected:
            issues.append("non_sequential_clauses")

        if len(numbers) != len(set(numbers)):
            issues.append("duplicate_clauses")

    for clause in parsed["clauses"]:
        letters = [
            p["letter"] for p in clause["points"]
        ]

        if not letters:
            continue

        if len(letters) != len(set(letters)):
            issues.append(
                f"duplicate_points_clause_{clause['number']}"
            )

        indices = [
            POINT_ORDER.index(x)
            for x in letters
            if x in POINT_ORDER
        ]

        if len(indices) != len(letters) or indices != list(
            range(len(letters))
        ):
            issues.append(
                f"non_sequential_points_clause_{clause['number']}"
            )

    return list(dict.fromkeys(issues))


def main():
    store = load_json(STORE_PATH)
    correction_config = load_json(CORRECTIONS_PATH)

    articles = store["articles"]
    rules = correction_config["corrections"]

    output_articles = []
    audit_articles = []

    for article in articles:
        number = int(article["article_number"])

        article = dict(article)
        article["article_number"] = number

        corrected_text = apply_corrections(
            article, rules
        )

        parsed = parse_article(corrected_text)
        issues = audit_article(parsed)

        article["body_corrected"] = corrected_text
        article["preamble"] = parsed["preamble"]
        article["clauses"] = parsed["clauses"]
        article["ignored_noise"] = parsed["ignored_noise"]

        article["structure_status"] = (
            "needs_review" if issues else "candidate"
        )

        output_articles.append(article)

        audit_articles.append({
            "article_number": number,
            "clause_count": len(parsed["clauses"]),
            "point_count": sum(
                len(c["points"])
                for c in parsed["clauses"]
            ),
            "clause_numbers": [
                c["number"] for c in parsed["clauses"]
            ],
            "issues": issues
        })

    summary = {
        "article_count": len(output_articles),
        "total_clauses": sum(
            a["clause_count"] for a in audit_articles
        ),
        "total_points": sum(
            a["point_count"] for a in audit_articles
        ),
        "articles_with_issues": sum(
            bool(a["issues"]) for a in audit_articles
        ),
        "correction_count": len(rules)
    }

    structured_store = dict(store)
    structured_store["articles"] = output_articles

    OUTPUT_PATH.write_text(
        json.dumps(
            structured_store,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    AUDIT_PATH.write_text(
        json.dumps(
            {
                "summary": summary,
                "articles": audit_articles
            },
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("=" * 60)
    print("CLAUSE PARSER V3")
    print("=" * 60)

    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nOutput:", OUTPUT_PATH)
    print("Audit:", AUDIT_PATH)

    print("\nIMPORTANT ARTICLES")

    for number in [3, 10, 102, 136, 141, 188, 204]:
        result = next(
            a for a in audit_articles
            if a["article_number"] == number
        )

        print(
            f"Dieu {number}: "
            f"{result['clause_numbers']} "
            f"| issues={result['issues']}"
        )


if __name__ == "__main__":
    main()
