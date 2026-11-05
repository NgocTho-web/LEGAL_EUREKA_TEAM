
import json
from pathlib import Path

BASE = Path("data/documents/processed")

with (BASE / "legal_document_store.json").open(
    encoding="utf-8"
) as f:
    store = json.load(f)

with (BASE / "verified_ocr_corrections.json").open(
    encoding="utf-8"
) as f:
    config = json.load(f)

articles = {
    int(a["article_number"]): a
    for a in store["articles"]
}

errors = []

for rule in config["corrections"]:
    number = rule["article"]
    article = articles.get(number)

    if article is None:
        errors.append(f"Dieu {number}: khong ton tai")
        continue

    text = article["body_raw"]
    count = text.count(rule["find"])

    if count != 1:
        errors.append(
            f"Dieu {number}: tim thay {count} lan - "
            f"{rule['find']}"
        )
    else:
        print(f"PASS: Dieu {number}")

if errors:
    print("\nCAN KIEM TRA:")
    for error in errors:
        print("-", error)
    raise SystemExit(1)

print("\nTat ca quy tac deu khop duy nhat.")
print("Chua thay doi du lieu goc.")
