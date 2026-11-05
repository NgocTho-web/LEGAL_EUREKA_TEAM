
from pathlib import Path
import pymupdf

pdf_path = Path(
    "data/documents/source/luat_dat_dai_2013.pdf"
)

with pymupdf.open(pdf_path) as doc:
    total_pages = len(doc)
    pages_with_text = []
    pages_without_text = []

    for index, page in enumerate(doc):
        text = page.get_text("text").strip()

        if len(text) >= 30:
            pages_with_text.append(index + 1)
        else:
            pages_without_text.append(index + 1)

    print("=== PDF SCAN CHECK ===")
    print("Total pages:", total_pages)
    print("Pages with text:", len(pages_with_text))
    print("Pages without text:", len(pages_without_text))
    print("First pages with text:", pages_with_text[:20])
    print("First pages without text:", pages_without_text[:20])
