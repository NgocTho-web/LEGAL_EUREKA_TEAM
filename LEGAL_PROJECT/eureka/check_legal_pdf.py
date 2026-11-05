
from pathlib import Path
import fitz

pdf_path = Path(
    "data/documents/source/luat_dat_dai_2013.pdf"
)

if not pdf_path.exists():
    raise FileNotFoundError(pdf_path)

doc = fitz.open(str(pdf_path))

print("=== PDF INFORMATION ===")
print("File:", pdf_path)
print("Total pages:", len(doc))

print("\n=== FIRST 3 PAGES ===")

for page_index in range(min(3, len(doc))):
    text = doc[page_index].get_text("text")

    print(f"\n--- PAGE {page_index + 1} ---")
    print("Characters:", len(text.strip()))
    print(text[:1500])

print("\n=== ARTICLE 110 SEARCH ===")

found = False

for page_index in range(len(doc)):
    text = doc[page_index].get_text("text")

    if "Điều 110" in text or "Điều  110" in text:
        found = True

        print("Found on page:", page_index + 1)
        print(text[:2500])
        break

if not found:
    print(
        "Không tìm thấy Điều 110 bằng tìm kiếm văn bản. "
        "PDF có thể là bản scan hoặc văn bản bị lỗi mã hóa."
    )

doc.close()
