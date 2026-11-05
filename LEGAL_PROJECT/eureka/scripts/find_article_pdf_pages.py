
import json
from pathlib import Path

STORE_PATH = Path(
    "data/documents/processed/legal_document_store.json"
)

TARGET_ARTICLES = [3, 10, 102, 136, 141, 188, 204]


def main():
    with STORE_PATH.open(encoding="utf-8") as f:
        store = json.load(f)

    articles = {
        int(a["article_number"]): a
        for a in store["articles"]
    }

    print("=" * 65)
    print("PDF PAGE LOOKUP - LUAT DAT DAI 2013")
    print("=" * 65)

    for number in TARGET_ARTICLES:
        article = articles.get(number)

        if not article:
            print(f"Dieu {number}: KHONG TIM THAY")
            continue

        source = article.get("source", {})

        print(f"\nDIEU {number}")
        print("Source:", json.dumps(
            source,
            ensure_ascii=False,
            indent=2
        ))

    print("\nLuu y: pdf_page la so trang PDF,")
    print("khong nhat thiet la so trang in tren van ban.")


if __name__ == "__main__":
    main()
