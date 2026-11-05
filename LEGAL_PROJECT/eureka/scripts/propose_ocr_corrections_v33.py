
import json
from pathlib import Path

BASE = Path("data/documents/processed")
STORE = BASE / "legal_document_store.json"
OUTPUT = BASE / "ocr_correction_proposals_v33.json"

proposals = [
    (32, "__b) Xây dựng", "b) Xây dựng"),
    (100, "; b) Giấy chứng nhận", "b) Giấy chứng nhận"),
    (100, ".g Giấy tờ chuyển nhượng", "d) Giấy tờ chuyển nhượng"),
    (169, "¡) Tổ chức, hộ gia đình", "i) Tổ chức, hộ gia đình"),
    (169, "Ú) Cộng đồng dân cư", "l) Cộng đồng dân cư"),
    (183, "_b) Thế chấp", "b) Thế chấp"),
    (184, ": _. 4. Doanh nghiệp liên doanh", "4. Doanh nghiệp liên doanh"),
    (186, "h c) Thế chấp nhà ở", "c) Thế chấp nhà ở"),
    (186, "e) Trong trường hợp chưa chuyển nhượng",
          "c) Trong trường hợp chưa chuyển nhượng"),
    (189, "ĐI a) Tài sản gắn liền", "a) Tài sản gắn liền"),
    (189, '"4, Đối với trường hợp thuê đất',
          "4. Đối với trường hợp thuê đất"),
    (195, "__b) Thủ tục đăng ký đất đai",
          "b) Thủ tục đăng ký đất đai"),
    (200, "' a) Thông tin về quy hoạch",
          "a) Thông tin về quy hoạch"),
]

data = json.loads(STORE.read_text(encoding="utf-8"))

articles = {
    int(a["article_number"]): a
    for a in data["articles"]
}

results = []

for number, old, new in proposals:
    count = articles[number]["body_raw"].count(old)

    results.append({
        "article": number,
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

print("OCR CORRECTION PROPOSALS V3.3")
print("=" * 50)

for item in results:
    status = "MATCH" if item["match_count"] == 1 else "CHECK"
    print(
        f"{status}: Dieu {item['article']} "
        f"({item['match_count']} matches)"
    )

print("\nTotal proposals:", len(results))
print("Saved:", OUTPUT)
print("Original OCR unchanged.")


if __name__ == "__main__":
    main = None
    # Run proposal generation without modifying source OCR.
