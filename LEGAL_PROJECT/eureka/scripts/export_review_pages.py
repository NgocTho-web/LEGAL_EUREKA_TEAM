
from pathlib import Path
from pypdf import PdfReader, PdfWriter

SOURCE = Path("data/documents/source/luat_dat_dai_2013.pdf")
OUTPUT = Path("data/documents/processed/ocr_review_pages.pdf")

PAGE_RANGES = [
    (1, 3),
    (6, 7),
    (59, 60),
    (79, 80),
    (81, 82),
    (111, 112),
    (119, 120),
]

def main():
    reader = PdfReader(str(SOURCE))
    writer = PdfWriter()

    pages = sorted({
        page
        for start, end in PAGE_RANGES
        for page in range(start, end + 1)
    })

    for page in pages:
        if not 1 <= page <= len(reader.pages):
            raise ValueError(f"Trang PDF khong hop le: {page}")

        writer.add_page(reader.pages[page - 1])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("wb") as f:
        writer.write(f)

    print("Tong trang PDF goc:", len(reader.pages))
    print("So trang da xuat:", len(pages))
    print("Cac trang:", pages)
    print("Da luu:", OUTPUT)

if __name__ == "__main__":
    main()
