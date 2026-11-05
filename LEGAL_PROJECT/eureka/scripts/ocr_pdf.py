
import os
import json
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = BASE_DIR / "data/documents/source/luat_dat_dai_2013.pdf"
OUTPUT_DIR = BASE_DIR / "data/documents/ocr"

TESSERACT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

POPPLER_PATH = Path(
    r"C:\Users\ngoct_tp0cae4\AppData\Local\Microsoft\WinGet\Packages"
    r"\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\poppler-25.07.0\Library\bin"
)

TESSDATA_DIR = BASE_DIR / "data/ocr_models"

TOTAL_PAGES = 123
BATCH_SIZE = 5
DPI = 300

LANGUAGE = "vie"
OCR_CONFIG = "--oem 1 --psm 6"


# ==========================================
# 2. INITIALIZATION
# ==========================================

def initialize():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy PDF: {PDF_PATH}")

    if not TESSERACT_PATH.exists():
        raise FileNotFoundError("Không tìm thấy Tesseract.")

    if not POPPLER_PATH.exists():
        raise FileNotFoundError("Không tìm thấy Poppler.")

    if not (TESSDATA_DIR / "vie.traineddata").exists():
        raise FileNotFoundError("Không tìm thấy dữ liệu OCR tiếng Việt.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)
    os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)


# ==========================================
# 3. OCR ONE PAGE
# ==========================================

def recognize_page(image, page_number):
    text = pytesseract.image_to_string(
        image,
        lang=LANGUAGE,
        config=OCR_CONFIG
    )

    return {
        "document_id": "luat_dat_dai_2013",
        "document_name": "Luật Đất đai 2013",
        "source_file": PDF_PATH.name,
        "pdf_page": page_number,
        "text": text.strip(),
        "ocr_engine": "Tesseract",
        "ocr_language": LANGUAGE,
        "ocr_dpi": DPI,
        "ocr_status": "raw"
    }


# ==========================================
# 4. PROCESS ALL PAGES
# ==========================================

def main():
    initialize()

    jsonl_path = OUTPUT_DIR / "luat_dat_dai_2013_ocr.jsonl"
    text_path = OUTPUT_DIR / "luat_dat_dai_2013_ocr.txt"

    print("Bắt đầu OCR toàn bộ tài liệu.")
    print(f"Tổng số trang: {TOTAL_PAGES}")
    print(f"Độ phân giải: {DPI} DPI")
    print(f"Số trang mỗi đợt: {BATCH_SIZE}")

    with (
        jsonl_path.open("w", encoding="utf-8") as jsonl_file,
        text_path.open("w", encoding="utf-8") as text_file
    ):

        for start_page in range(1, TOTAL_PAGES + 1, BATCH_SIZE):

            end_page = min(
                start_page + BATCH_SIZE - 1,
                TOTAL_PAGES
            )

            print(
                f"\nĐang xử lý trang {start_page} đến {end_page}..."
            )

            images = convert_from_path(
                str(PDF_PATH),
                dpi=DPI,
                first_page=start_page,
                last_page=end_page,
                poppler_path=str(POPPLER_PATH)
            )

            for offset, image in enumerate(images):
                page_number = start_page + offset

                print(
                    f"  OCR trang {page_number}/{TOTAL_PAGES}..."
                )

                record = recognize_page(image, page_number)

                # Lưu dữ liệu có cấu trúc JSONL
                jsonl_file.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )
                jsonl_file.flush()

                # Lưu bản văn bản dễ đọc
                text_file.write(
                    f"\n\n{'=' * 50}\n"
                    f"PDF PAGE: {page_number}\n"
                    f"{'=' * 50}\n"
                )
                text_file.write(record["text"])
                text_file.flush()

            images.clear()

    print("\n================================")
    print("HOÀN TẤT OCR TOÀN BỘ TÀI LIỆU")
    print(f"JSONL: {jsonl_path}")
    print(f"TEXT:  {text_path}")
    print("================================")


if __name__ == "__main__":
    main()
