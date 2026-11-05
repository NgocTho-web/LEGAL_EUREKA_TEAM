
import json
import re
from pathlib import Path
from collections import Counter

OCR_FILE = Path(
    "data/documents/ocr/luat_dat_dai_2013_ocr.jsonl"
)

text_parts = []

with OCR_FILE.open("r", encoding="utf-8") as file:
    for line in file:
        record = json.loads(line)
        text_parts.append(
            f"\n[PDF PAGE: {record['pdf_page']}]\n"
            + record["text"]
        )

full_text = "\n".join(text_parts)

patterns = {
    "Chương": r"(?im)^\s*CHƯƠNG\s+([IVXLCDM]+)\b",
    "Điều": r"(?im)^\s*Điều\s+\d+\s*[.:]",
    "Khoản": r"(?m)^\s*\d+\.\s+\S",
    "Điểm": r"(?m)^\s*[a-zđ]\)\s*",
}

print("===== THỐNG KÊ CẤU TRÚC OCR =====")

for name, pattern in patterns.items():
    matches = re.findall(pattern, full_text)
    print(f"{name}: {len(matches)}")

print("\n===== DANH SÁCH TIÊU ĐỀ ĐIỀU =====")

article_pattern = re.compile(
    r"(?im)^\s*(Điều\s+\d+\s*[.:].*)$"
)

articles = article_pattern.findall(full_text)

for article in articles:
    print(article.strip())

print("\n===== MẪU CÁC DÒNG CÓ KHOẢN VÀ ĐIỂM =====")

for line in full_text.splitlines():
    if re.match(r"^\s*\d+\.\s+\S", line) or re.match(
        r"^\s*[a-zđ]\)\s*", line
    ):
        print(line.strip()[:180])



# ==========================================
# 5. EXPORT SUMMARY REPORT
# ==========================================

from pathlib import Path
from collections import Counter

report_path = Path(
    "data/documents/ocr/ocr_structure_report.txt"
)

lines = full_text.splitlines()

# Thống kê số lượng tiêu đề Điều
article_matches = list(
    re.finditer(
        r"(?im)^\s*(Điều\s+\d+\s*[.:].*)$",
        full_text
    )
)

# Thống kê chương
chapter_matches = list(
    re.finditer(
        r"(?im)^\s*CHƯƠNG\s+([IVXLCDM]+)\b",
        full_text
    )
)

# Thống kê khoản và điểm
clause_matches = list(
    re.finditer(
        r"(?m)^\s*\d+\.\s+\S",
        full_text
    )
)

point_matches = list(
    re.finditer(
        r"(?m)^\s*[a-zđ]\)\s*",
        full_text
    )
)

# Tìm các Điều được nhận diện
article_numbers = re.findall(
    r"(?im)^\s*Điều\s+(\d+)",
    full_text
)

counter = Counter(article_numbers)

with report_path.open("w", encoding="utf-8") as f:
    f.write("===== OCR STRUCTURE REPORT =====\n\n")

    f.write(f"Tổng số ký tự: {len(full_text)}\n")
    f.write(f"Số Chương nhận diện: {len(chapter_matches)}\n")
    f.write(f"Số tiêu đề Điều nhận diện: {len(article_matches)}\n")
    f.write(f"Số dòng có dạng Khoản: {len(clause_matches)}\n")
    f.write(f"Số dòng có dạng Điểm: {len(point_matches)}\n")

    f.write("\n===== ĐIỀU NHẬN DIỆN =====\n")

    for match in article_matches:
        f.write(match.group(1).strip() + "\n")

    f.write("\n===== ĐIỀU BỊ NHẬN DIỆN TRÙNG =====\n")

    for number, count in sorted(
        counter.items(),
        key=lambda x: int(x[0])
    ):
        if count > 1:
            f.write(f"Điều {number}: {count} lần\n")

    f.write("\n===== MỘT SỐ DÒNG OCR MẪU =====\n")

    samples = 0

    for line in lines:
        if (
            re.match(r"^\s*\d+\.\s+\S", line)
            or re.match(r"^\s*[a-zđ]\)\s*", line)
        ):
            f.write(line.strip()[:200] + "\n")
            samples += 1

            if samples >= 30:
                break

print(f"\nĐã xuất báo cáo: {report_path}")
