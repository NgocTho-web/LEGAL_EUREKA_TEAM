
import json
from pathlib import Path

BASE = Path("data/documents/processed")
STORE = BASE / "legal_document_store.json"
OUTPUT = BASE / "ocr_correction_proposals_v31.json"

proposals = [
    (22, "l 4. Quản lý quy hoạch", "4. Quản lý quy hoạch"),
    (22, "l 12. Thanh tra", "12. Thanh tra"),
    (34, "b Việc thống kê đất đai", "b) Việc thống kê đất đai"),
    (40, "- 4. Nội dung kế hoạch", "4. Nội dung kế hoạch"),
    (43, ". 3. Cơ quan có trách nhiệm", "3. Cơ quan có trách nhiệm"),
    (58, ": ]. Đối với dự án", "1. Đối với dự án"),
    (72, "Ệ 7. Việc bồi thường", "7. Việc bồi thường"),
    (75, "Ĩ 1. Hộ gia đình", "1. Hộ gia đình"),
    (79, "| _ 3, Tổ chức kinh tế", "3. Tổ chức kinh tế"),
    (80, "; ; 1. Hộ gia đình", "1. Hộ gia đình"),
    (84, "„1 Hộ gia đình", "1. Hộ gia đình"),
    (95, "1) Chia tách quyền", "i) Chia tách quyền"),
    (118, "2 Các trường hợp không đấu giá", "2. Các trường hợp không đấu giá"),
    (160, "4 2. Việc sử dụng đất tín ngưỡng", "2. Việc sử dụng đất tín ngưỡng"),
    (185, "Ì 1. Người Việt Nam", "1. Người Việt Nam"),
    (192, "Ế 1. Hộ gia đình", "1. Hộ gia đình"),
    (201, "ị 3. Thanh tra chuyên ngành", "3. Thanh tra chuyên ngành"),
    (207, "9) Lợi dụng chức vụ", "a) Lợi dụng chức vụ"),
]

store = json.loads(STORE.read_text(encoding="utf-8"))
articles = {
    int(a["article_number"]): a
    for a in store["articles"]
}

results = []

for number, old, new in proposals:
    article = articles.get(number)
    count = (
        article["body_raw"].count(old)
        if article else 0
    )

    results.append({
        "article": number,
        "find": old,
        "replace": new,
        "match_count": count,
        "status": "pending_pdf_verification"
    })

OUTPUT.write_text(
    json.dumps(
        {"proposals": results},
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("OCR CORRECTION PROPOSALS V3.1")
print("=" * 50)

for item in results:
    status = (
        "MATCH" if item["match_count"] == 1
        else "CHECK"
    )
    print(
        f"{status}: Dieu {item['article']} "
        f"({item['match_count']} matches)"
    )

print("\nSaved:", OUTPUT)
print("No source files modified.")
