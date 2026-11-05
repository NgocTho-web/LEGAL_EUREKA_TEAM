
import json
import re
from pathlib import Path
from datetime import datetime, timezone


# =====================================================
# 1. CONFIG
# =====================================================

OCR_FILE = Path(
    "data/documents/ocr/luat_dat_dai_2013_ocr.jsonl"
)

AUDIT_FILE = Path(
    "data/documents/processed/article_audit.json"
)

OUTPUT_FILE = Path(
    "data/documents/processed/legal_document_store.json"
)

DOCUMENT_ID = "luat_dat_dai_2013"

EXPECTED_ARTICLES = set(range(1, 213))


# =====================================================
# 2. LOAD JSON
# =====================================================

def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_ocr_pages(path):
    pages = []

    with path.open("r", encoding="utf-8") as f:
        for file_line, raw in enumerate(f, start=1):
            if not raw.strip():
                continue

            try:
                page = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"JSONL không hợp lệ tại dòng {file_line}"
                ) from exc

            if not isinstance(page.get("pdf_page"), int):
                raise ValueError(
                    f"Thiếu pdf_page tại dòng {file_line}"
                )

            if not isinstance(page.get("text"), str):
                raise ValueError(
                    f"Thiếu text tại dòng {file_line}"
                )

            pages.append(page)

    pages.sort(key=lambda x: x["pdf_page"])

    page_numbers = [p["pdf_page"] for p in pages]

    if len(page_numbers) != len(set(page_numbers)):
        raise ValueError("Có trang PDF bị trùng trong OCR")

    return pages


# =====================================================
# 3. CHUYỂN OCR THÀNH DANH SÁCH DÒNG
# =====================================================

def flatten_ocr_lines(pages):
    lines = []

    for page in pages:
        pdf_page = page["pdf_page"]

        for line_number, text in enumerate(
            page["text"].splitlines(),
            start=1
        ):
            lines.append({
                "pdf_page": pdf_page,
                "line_number": line_number,
                "text": text
            })

    return lines


# =====================================================
# 4. KIỂM TRA AUDIT
# =====================================================

def validate_audit(audit):
    headings = audit.get("heading_candidates", [])

    numbers = [
        item["article_number"]
        for item in headings
    ]

    if len(headings) != 212:
        raise ValueError(
            f"Audit có {len(headings)} tiêu đề, cần 212"
        )

    if set(numbers) != EXPECTED_ARTICLES:
        missing = sorted(EXPECTED_ARTICLES - set(numbers))
        extra = sorted(set(numbers) - EXPECTED_ARTICLES)

        raise ValueError(
            f"Audit chưa hợp lệ. Thiếu: {missing}; dư: {extra}"
        )

    if len(numbers) != len(set(numbers)):
        raise ValueError("Audit có số Điều trùng lặp")

    if audit.get("page_errors"):
        raise ValueError("Audit có lỗi đọc trang")

    return sorted(
        headings,
        key=lambda x: x["article_number"]
    )


# =====================================================
# 5. XÁC ĐỊNH VỊ TRÍ TIÊU ĐỀ
# =====================================================

def build_line_index(lines):
    return {
        (line["pdf_page"], line["line_number"]): index
        for index, line in enumerate(lines)
    }


def locate_headings(headings, lines):
    line_index = build_line_index(lines)
    located = []

    for heading in headings:
        key = (
            heading["pdf_page"],
            heading["line_number"]
        )

        if key not in line_index:
            raise ValueError(
                f"Không tìm thấy dòng OCR của Điều "
                f"{heading['article_number']}: {key}"
            )

        index = line_index[key]
        actual_line = lines[index]["text"].strip()
        audit_line = heading["raw_line"].strip()

        if actual_line != audit_line:
            raise ValueError(
                f"OCR và audit không khớp tại Điều "
                f"{heading['article_number']}"
            )

        located.append({
            **heading,
            "global_line_index": index
        })

    positions = [
        h["global_line_index"]
        for h in located
    ]

    if positions != sorted(positions):
        raise ValueError(
            "Thứ tự tiêu đề Điều không khớp thứ tự OCR"
        )

    return located


# =====================================================
# 6. XÂY DỰNG NỘI DUNG TỪNG ĐIỀU
# =====================================================

def build_articles(headings, lines):
    articles = []

    for i, heading in enumerate(headings):
        start = heading["global_line_index"]

        if i + 1 < len(headings):
            end = headings[i + 1]["global_line_index"]
        else:
            end = len(lines)

        article_lines = lines[start:end]

        # Giữ nguyên văn bản OCR, không tự sửa nội dung.
        raw_text = "\n".join(
            line["text"] for line in article_lines
        )

        # Không đưa dòng tiêu đề vào body.
        body_lines = article_lines[1:]

        body_text = "\n".join(
            line["text"] for line in body_lines
        )

        article_number = heading["article_number"]

        article = {
            "id": (
                f"{DOCUMENT_ID}_article_{article_number}"
            ),
            "document_id": DOCUMENT_ID,
            "article_number": article_number,
            "heading_raw": heading["raw_line"],
            "heading_text_ocr": heading["heading_text"],
            "text_raw": raw_text,
            "body_raw": body_text,
            "source": {
                "file": "luat_dat_dai_2013.pdf",
                "start_pdf_page": article_lines[0]["pdf_page"],
                "start_line": article_lines[0]["line_number"],
                "end_pdf_page": article_lines[-1]["pdf_page"],
                "end_line": article_lines[-1]["line_number"]
            },
            "ocr_status": "raw",
            "verification_status": "unverified",
            "heading_detection_status": "candidate",
            "clauses": [],
            "points": []
        }

        articles.append(article)

    return articles


# =====================================================
# 7. MAIN
# =====================================================

def main():
    print("=" * 65)
    print("BUILD LEGAL DOCUMENT STORE")
    print("=" * 65)

    if not OCR_FILE.exists():
        raise FileNotFoundError(OCR_FILE)

    if not AUDIT_FILE.exists():
        raise FileNotFoundError(AUDIT_FILE)

    pages = load_ocr_pages(OCR_FILE)
    audit = load_json(AUDIT_FILE)

    headings = validate_audit(audit)
    lines = flatten_ocr_lines(pages)
    located_headings = locate_headings(headings, lines)
    articles = build_articles(located_headings, lines)

    store = {
        "document_id": DOCUMENT_ID,
        "document_name": "Luật Đất đai 2013",
        "source_file": "luat_dat_dai_2013.pdf",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_type": "scanned_pdf_ocr",
        "ocr_status": "raw",
        "verification_status": "unverified",
        "article_count": len(articles),
        "articles": articles,
        "notes": [
            "Nội dung được trích từ OCR, chưa xác minh.",
            "Ranh giới Điều dựa trên heading_candidate.",
            "Chưa tách Khoản và Điểm.",
            "Chưa đối chiếu với Knowledge Graph Stage3."
        ]
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            store,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"Số trang OCR: {len(pages)}")
    print(f"Số Điều: {len(articles)}")
    print(f"Tổng dòng OCR: {len(lines)}")
    print(f"Đã lưu: {OUTPUT_FILE}")
    print("=" * 65)


if __name__ == "__main__":
    main()
