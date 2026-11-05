
import json
import re
from pathlib import Path
from collections import Counter

OCR_FILE = Path(
    "data/documents/ocr/luat_dat_dai_2013_ocr.jsonl"
)

full_text = []

with OCR_FILE.open("r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        full_text.append(
            f"\n[PDF PAGE: {record['pdf_page']}]\n"
            + record["text"]
        )

text = "\n".join(full_text)

# Tìm Điều kể cả khi OCR có khoảng trắng hoặc dấu câu bất thường
pattern = re.compile(
    r"Điều\s+(\d{1,3})\s*[.:：]?",
    re.IGNORECASE
)

numbers = [
    int(match.group(1))
    for match in pattern.finditer(text)
]

counts = Counter(numbers)

expected = set(range(1, 213))
detected = set(counts.keys())

missing = sorted(expected - detected)
duplicates = sorted(
    number for number, count in counts.items()
    if count > 1
)

print("===== AUDIT ĐIỀU LUẬT =====")
print("Số Điều khác nhau nhận diện:", len(detected))
print("Số lần xuất hiện tiêu đề/số Điều:", len(numbers))
print("Điều chưa tìm thấy:", missing)
print("Điều xuất hiện nhiều lần:", duplicates)

print("\n===== NGỮ CẢNH CÁC ĐIỀU CHƯA TÌM THẤY =====")

for number in missing:
    print(f"\nĐiều {number}:")
    matches = list(re.finditer(
        rf"Điều\s+{number}\b",
        text,
        re.IGNORECASE
    ))

    if not matches:
        print("  Không tìm thấy chuỗi tương ứng.")
