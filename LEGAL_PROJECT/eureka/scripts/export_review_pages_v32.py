
import json
from pathlib import Path
from pypdf import PdfReader, PdfWriter

BASE = Path("data/documents")

STORE = BASE / "processed/legal_document_store.json"
PROPOSALS = BASE / "processed/ocr_correction_proposals_v33.json"

PDF = BASE / "source/luat_dat_dai_2013.pdf"
OUTPUT_DIR = BASE / "processed/review_v33"

GROUP_SIZE = 6


def main():
    store = json.loads(STORE.read_text(encoding="utf-8"))
    proposals = json.loads(
        PROPOSALS.read_text(encoding="utf-8")
    )["proposals"]

    articles = {
        int(a["article_number"]): a
        for a in store["articles"]
    }

    numbers = sorted({
        int(p["article"])
        for p in proposals
    })

    reader = PdfReader(str(PDF))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    groups = [
        numbers[i:i + GROUP_SIZE]
        for i in range(0, len(numbers), GROUP_SIZE)
    ]

    for group_index, group in enumerate(groups, start=1):
        writer = PdfWriter()
        selected_pages = set()

        for number in group:
            source = articles[number]["source"]

            start = int(source["start_pdf_page"])
            end = int(source["end_pdf_page"])

            for page in range(start, end + 1):
                if not 1 <= page <= len(reader.pages):
                    raise ValueError(
                        f"Invalid PDF page: {page}"
                    )
                selected_pages.add(page)

        for page in sorted(selected_pages):
            writer.add_page(reader.pages[page - 1])

        output = (
            OUTPUT_DIR /
            f"ocr_review_v33_part{group_index}.pdf"
        )

        with output.open("wb") as f:
            writer.write(f)

        print(
            f"Part {group_index}: "
            f"Articles {group} | "
            f"{len(selected_pages)} pages"
        )
        print("Saved:", output)

    print("\nTotal articles:", len(numbers))
    print("Total PDF parts:", len(groups))
    print("Original PDF unchanged.")


if __name__ == "__main__":
    main()
