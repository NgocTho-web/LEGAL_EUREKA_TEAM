
import json
from pathlib import Path

path = Path(
    "data/documents/processed/"
    "structured_legal_document_store_v3.json"
)

data = json.loads(path.read_text(encoding="utf-8"))

print("=" * 60)
print("STRUCTURED LEGAL STORE SCHEMA")
print("=" * 60)

print("Top-level keys:", list(data.keys()))

articles = data["articles"]
print("Article count:", len(articles))

for number in [3, 100, 184, 188]:
    article = next(
        (a for a in articles
         if int(a["article_number"]) == number),
        None
    )

    if article is None:
        continue

    print(f"\nDIEU {number}")
    print("Article keys:", list(article.keys()))

    clauses = article.get("clauses", [])

    if clauses:
        clause = next(
            (c for c in clauses if c.get("points")),
            clauses[0]
        )

        print("Clause keys:", list(clause.keys()))

        print(
            "Clause sample:",
            json.dumps(
                clause,
                ensure_ascii=False,
                indent=2
            )[:1500]
        )

        points = clause.get("points", [])

        if points:
            print("Point keys:", list(points[0].keys()))
            print(
                "Point sample:",
                json.dumps(
                    points[0],
                    ensure_ascii=False,
                    indent=2
                )[:1000]
            )

print("\nInspection complete. No files modified.")
