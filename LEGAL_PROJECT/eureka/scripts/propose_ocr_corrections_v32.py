
import json
from pathlib import Path

BASE = Path("data/documents/processed")
STORE = BASE / "legal_document_store.json"
OUTPUT = BASE / "ocr_correction_proposals_v32.json"

# Chỉ sửa phần ký hiệu cấu trúc và vài ký tự liền kề.
# Tất cả vẫn cần đối chiếu PDF trước khi đánh dấu verified.
proposals = [
    (32, "©) Xây dựng báo cáo", "c) Xây dựng báo cáo"),
    (39, "ở) Nhu cầu sử dụng đất", "đ) Nhu cầu sử dụng đất"),
    (40, "bì Xác định diện tích", "b) Xác định diện tích"),
    (43, "- a) Việc lấy ý kiến", "a) Việc lấy ý kiến"),
    (46, "đ) Có sự điều chỉnh địa giới", "d) Có sự điều chỉnh địa giới"),
    (65, "ở) Đất ở trong khu vực", "đ) Đất ở trong khu vực"),
    (95, "]) Xác lập, thay đổi", "l) Xác lập, thay đổi"),
    (99, ") Người sử dụng đắt tách thửa", "i) Người sử dụng đắt tách thửa"),
    (100, "9) Giấy tờ hợp pháp", "c) Giấy tờ hợp pháp"),
    (103, "W— Đối với trường hợp không có giấy tờ", "5. Đối với trường hợp không có giấy tờ"),
    (106, "e) Người sử dụng đất, chủ sở hữu tài sản", "c) Người sử dụng đất, chủ sở hữu tài sản"),
    (115, "_..a) Khi xây dựng", "a) Khi xây dựng"),
    (115, ".b) Khi giải quyết", "b) Khi giải quyết"),
    (118, "e9) Giao đất ở cho cán bộ", "e) Giao đất ở cho cán bộ"),
    (121, "ũ d) Cơ sở dữ liệu quy hoạch", "d) Cơ sở dữ liệu quy hoạch"),
    (127, "i d) Trường hợp chuyên đât nông nghiệp", "d) Trường hợp chuyên đât nông nghiệp"),
    (151, "I 1. Đất sử dụng cho khu kinh tế", "1. Đất sử dụng cho khu kinh tế"),
    (165, "_1.Căn cứ vào quy hoạch", "1. Căn cứ vào quy hoạch"),
    (174, "h 3. Tổ chức sự nghiệp", "3. Tổ chức sự nghiệp"),
    (176, "_a) Trường hợp tổ chức kinh tế", "a) Trường hợp tổ chức kinh tế"),
    (177, "l a) Đất của tổ chức kinh tế", "a) Đất của tổ chức kinh tế"),
    (186, "' 1. Người Việt Nam định cư", "1. Người Việt Nam định cư"),
    (197, "| 2 Ủy ban nhân dân", "2. Ủy ban nhân dân"),
    (197, "; 4 Người sử dụng đất", "4. Người sử dụng đất"),
    (200, "_©) Thông tin từ quá trình giám sát", "c) Thông tin từ quá trình giám sát"),
]

data = json.loads(STORE.read_text(encoding="utf-8"))
articles = {
    int(a["article_number"]): a
    for a in data["articles"]
}

results = []

for article, old, new in proposals:
    count = articles[article]["body_raw"].count(old)

    results.append({
        "article": article,
        "find": old,
        "replace": new,
        "match_count": count,
        "verification_status": "pending_pdf_verification"
    })

OUTPUT.write_text(
    json.dumps(
        {"proposals": results},
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("OCR CORRECTION PROPOSALS V3.2")
print("=" * 50)

for item in results:
    status = "MATCH" if item["match_count"] == 1 else "CHECK"
    print(
        f"{status}: Dieu {item['article']} "
        f"({item['match_count']} matches)"
    )

print("\nTotal proposals:", len(results))
print("Saved:", OUTPUT)
print("Source OCR unchanged.")
