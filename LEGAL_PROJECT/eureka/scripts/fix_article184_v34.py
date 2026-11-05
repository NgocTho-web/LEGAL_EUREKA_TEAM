
import json
from pathlib import Path

BASE = Path("data/documents/processed")

STORE = BASE / "legal_document_store.json"
OUTPUT = BASE / "ocr_correction_proposals_v34.json"

proposals = [
    {
        "article": 184,
        "find": "L a) Quyền và nghĩa vụ",
        "replace": "a) Quyền và nghĩa vụ",
    },
    {
        "article": 184,
        "find": "N c) Quyền và nghĩa vụ",
        "replace": "c) Quyền và nghĩa vụ",
    },
]

data = json.loads(STORE.read_text(encoding="utf-8"))

article = next(
    a for a in data["articles"]
    if int(a["article_number"]) == 184
)

results = []

for proposal in proposals:
    count = article["body_raw"].count(proposal["find"])

    results.append({
        **proposal,
        "match_count": count,
        "verification_status": "pending_pdf_verification",
    })

OUTPUT.write_text(
    json.dumps(
        {"proposals": results},
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("OCR CORRECTION PROPOSALS V3.4")
print("=" * 50)

for item in results:
    status = "MATCH" if item["match_count"] == 1 else "CHECK"

    print(
        f"{status}: Dieu {item['article']} "
        f"({item['match_count']} matches)"
    )

print("Saved:", OUTPUT)
print("Original OCR unchanged.")
