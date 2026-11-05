
import json
from pathlib import Path
from pypdf import PdfReader, PdfWriter

BASE = Path("data/documents")

SOURCE = BASE / "source/luat_dat_dai_2013.pdf"
STORE = BASE / "processed/legal_document_store.json"
PROPOSALS = BASE / "processed/ocr_correction_proposals_v31.json"
OUTPUT_DIR = BASE / "processed/review_v31"


def main():
    store = json.loads(
        STORE.read_text(encoding="utf-8")
    )

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

    reader = PdfReader(str(SOURCE))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Chia thành các nhóm nhỏ để dễ đối chiếu
    groups = [
        numbers[i:i + 6]
        for i in range(0, len(numbers), 6)
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
                        f"Invalid PDF page {page}"
                    )
                selected_pages.add(page)

        for page in sorted(selected_pages):
            writer.add_page(reader.pages[page - 1])

        output = (
            OUTPUT_DIR /
            f"ocr_review_v31_part{group_index}.pdf"
        )

        with output.open("wb") as f:
            writer.write(f)

        print(
            f"Part {group_index}: "
            f"Dieu {group} | "
            f"{len(selected_pages)} PDF pages"
        )
        print("Saved:", output)


if __name__ == "__main__":
    main()
