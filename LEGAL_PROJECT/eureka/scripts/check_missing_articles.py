
import json
import re
from pathlib import Path

OCR_FILE = Path("data/documents/ocr/luat_dat_dai_2013_ocr.jsonl")

MISSING = [2, 43, 177, 180, 182, 185, 186, 190, 192, 203, 204, 209]

with OCR_FILE.open("r", encoding="utf-8") as f:
    pages = [json.loads(line) for line in f if line.strip()]

for article in MISSING:
    print(f"\n{'=' * 65}")
    print(f"ĐIỀU {article}")
    print("=" * 65)

    found = False

    # Tìm mọi dòng có chứa từ "Điều", kể cả khi OCR nhận sai dấu
    for page in pages:
        lines = page.get("text", "").splitlines()

        for i, line in enumerate(lines):
            normalized = line.lower()

            if "điều" in normalized or "điêu" in normalized:
                # Hiển thị dòng có số gần với số điều cần tìm
                numbers = re.findall(r"\d{1,3}", line)

                if any(
                    abs(int(number) - article) <= 1
                    for number in numbers
                ):
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)

                    print(f"\nPDF page: {page.get('pdf_page')}")
                    print("\n".join(lines[start:end]))
                    found = True

    if not found:
        print("Không tìm thấy dòng gần khớp.")
