
import argparse
import json
import os
from pathlib import Path

from neo4j import GraphDatabase


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STORE_PATH = (
    PROJECT_ROOT
    / "data"
    / "documents"
    / "processed"
    / "structured_legal_document_store_v3.json"
)

LAW_PREFIX = "vn_law_2013_45_2013_qh13"

EXPECTED_DOCUMENT_ID = "luat_dat_dai_2013"


def load_store():
    with STORE_PATH.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if data.get("document_id") != EXPECTED_DOCUMENT_ID:
        raise ValueError("Document ID does not match expected law")

    if not isinstance(data.get("articles"), list):
        raise ValueError("Missing articles list")

    return data


def prepare_records(data):
    records = []
    seen_ids = set()

    for article in data["articles"]:
        number = article.get("article_number")

        if type(number) is not int or number <= 0:
            raise ValueError(
                f"Invalid article number: {number}"
            )

        node_id = f"{LAW_PREFIX}_article_{number}"

        if node_id in seen_ids:
            raise ValueError(f"Duplicate ID: {node_id}")

        seen_ids.add(node_id)

        source = article.get("source") or {}

        records.append({
            "id": node_id,
            "article_number": number,
            "ocr_content": article.get("body_corrected")
                or article.get("body_raw")
                or "",
            "ocr_heading": article.get("heading_raw") or "",
            "ocr_source_file": source.get("file") or
                data.get("source_file"),
            "ocr_start_page": source.get("start_pdf_page"),
            "ocr_end_page": source.get("end_pdf_page"),
            "ocr_verification_status":
                article.get("verification_status", "unverified"),
            "ocr_structure_status":
                article.get("structure_status", "candidate"),
        })

    return records


def inspect_existing(tx, ids):
    result = tx.run(
        """
        UNWIND $ids AS node_id
        OPTIONAL MATCH (n:LegalEntity {id: node_id})
        RETURN
            node_id AS id,
            n.type AS node_type,
            n.ocr_content AS existing_content
        """,
        ids=ids,
    )

    return [dict(row) for row in result]


def write_batch(tx, records):
    result = tx.run(
        """
        UNWIND $records AS row
        MATCH (n:LegalEntity {id: row.id})
        WHERE n.type = 'LegalArticle'
          AND n.ocr_content IS NULL
        SET
            n.ocr_content = row.ocr_content,
            n.ocr_heading = row.ocr_heading,
            n.ocr_source_file = row.ocr_source_file,
            n.ocr_start_page = row.ocr_start_page,
            n.ocr_end_page = row.ocr_end_page,
            n.ocr_verification_status =
                row.ocr_verification_status,
            n.ocr_structure_status =
                row.ocr_structure_status
        RETURN count(n) AS updated
        """,
        records=records,
    )

    return result.single()["updated"]


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write to Neo4j. Default is dry-run.",
    )

    parser.add_argument(
        "--article",
        type=int,
        default=None,
        help="Sync only one article number.",
    )

    args = parser.parse_args()

    data = load_store()
    records = prepare_records(data)

    if args.article is not None:
        records = [
            r for r in records
            if r["article_number"] == args.article
        ]

    if not records:
        raise ValueError("No records selected")

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not password:
        raise ValueError(
            "Set NEO4J_PASSWORD before running"
        )

    print("=== EUREKA LEGAL KG SYNC ===")
    print("Mode:", "APPLY" if args.apply else "DRY-RUN")
    print("Selected records:", len(records))
    print("Neo4j URI:", uri)

    driver = GraphDatabase.driver(
        uri,
        auth=(user, password),
    )

    try:
        driver.verify_connectivity()

        with driver.session() as session:
            existing = session.execute_read(
                inspect_existing,
                [r["id"] for r in records],
            )

            index = {r["id"]: r for r in existing}

            eligible = []
            missing = []
            wrong_type = []
            already_populated = []

            for record in records:
                node = index.get(record["id"])

                if not node or node["node_type"] is None:
                    missing.append(record["id"])
                    continue

                if node["node_type"] != "LegalArticle":
                    wrong_type.append(record["id"])
                    continue

                if node["existing_content"] is not None:
                    already_populated.append(record["id"])
                    continue

                if not record["ocr_content"].strip():
                    continue

                eligible.append(record)

            print("Eligible:", len(eligible))
            print("Missing:", len(missing))
            print("Wrong type:", len(wrong_type))
            print("Already populated:", len(already_populated))

            print("\nFirst eligible IDs:")
            for record in eligible[:10]:
                print(" -", record["id"])

            if missing:
                print("\nMissing IDs:")
                for node_id in missing[:10]:
                    print(" -", node_id)

            if not args.apply:
                print("\nDRY-RUN COMPLETE")
                print("No Neo4j data was modified.")
                return

            if missing or wrong_type:
                raise RuntimeError(
                    "Aborted: graph IDs/types do not fully match"
                )

            updated = 0

            for offset in range(0, len(eligible), 25):
                batch = eligible[offset:offset + 25]

                updated += session.execute_write(
                    write_batch,
                    batch,
                )

            print("\nUPDATED:", updated)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
