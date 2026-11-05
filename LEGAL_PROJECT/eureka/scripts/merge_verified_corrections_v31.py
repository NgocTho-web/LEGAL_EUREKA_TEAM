
import json
import shutil
from pathlib import Path
from datetime import datetime

BASE = Path("data/documents/processed")

VERIFIED = BASE / "verified_ocr_corrections.json"
PROPOSALS = BASE / "ocr_correction_proposals_v34.json"
STORE = BASE / "legal_document_store.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    verified_data = read_json(VERIFIED)
    proposal_data = read_json(PROPOSALS)
    store_data = read_json(STORE)

    existing = verified_data["corrections"]
    proposals = proposal_data["proposals"]

    articles = {
        int(a["article_number"]): a
        for a in store_data["articles"]
    }

    merged = list(existing)
    keys = {
        (int(r["article"]), r["find"])
        for r in merged
    }

    added = 0

    for p in proposals:
        number = int(p["article"])
        old = p["find"]
        new = p["replace"]

        if number not in articles:
            raise ValueError(f"Missing article {number}")

        if articles[number]["body_raw"].count(old) != 1:
            raise ValueError(
                f"OCR mismatch in article {number}: {old}"
            )

        key = (number, old)

        if key in keys:
            current = next(
                r for r in merged
                if (int(r["article"]), r["find"]) == key
            )
            if current["replace"] != new:
                raise ValueError(
                    f"Conflicting correction: article {number}"
                )
            continue

        merged.append({
            "article": number,
            "find": old,
            "replace": new,
            "verification_status": "verified",
            "verification_source": "ocr_review_v33_part1_pdf_article184"
        })

        keys.add(key)
        added += 1

    # Validate all corrections without modifying source data.
    for number in articles:
        text = articles[number]["body_raw"]

        for rule in merged:
            if int(rule["article"]) != number:
                continue

            if text.count(rule["find"]) != 1:
                raise ValueError(
                    f"Sequential mismatch: article {number}"
                )

            text = text.replace(
                rule["find"], rule["replace"], 1
            )

    # Backup before updating the correction configuration.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BASE / f"verified_ocr_corrections_{timestamp}.bak.json"

    shutil.copy2(VERIFIED, backup)

    verified_data["corrections"] = merged

    VERIFIED.write_text(
        json.dumps(
            verified_data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("MERGE VERIFIED CORRECTIONS V3.1")
    print("=" * 50)
    print("Existing:", len(existing))
    print("Added:", added)
    print("Total:", len(merged))
    print("Backup:", backup)
    print("Source OCR unchanged.")


if __name__ == "__main__":
    main()
