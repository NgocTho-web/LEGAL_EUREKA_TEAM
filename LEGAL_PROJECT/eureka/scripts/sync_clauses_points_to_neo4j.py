
import argparse
import json
import os
import sys
from pathlib import Path

from neo4j import GraphDatabase

STORE = Path(
    "data/documents/processed/structured_legal_document_store_v3.json"
)
PREFIX = "vn_law_2013_45_2013_qh13"


def load_records(article_filter=None):
    with STORE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    records = []

    for article in data["articles"]:
        article_no = int(article["article_number"])

        if article_filter is not None and article_no != article_filter:
            continue

        article_id = f"{PREFIX}_article_{article_no}"
        source = article.get("source") or {}
        source_file = source.get("file") or data.get("source_file")

        for clause in article.get("clauses", []):
            clause_no = int(clause["number"])
            clause_id = f"{article_id}_clause_{clause_no}"

            records.append({
                "id": clause_id,
                "type": "LegalClause",
                "text": clause.get("text", ""),
                "source_file": source_file,
                "verification": "unverified",
            })

            for point in clause.get("points", []):
                letter = str(point["letter"])
                point_id = f"{clause_id}_point_{letter}"

                records.append({
                    "id": point_id,
                    "type": "LegalPoint",
                    "text": point.get("text", ""),
                    "source_file": source_file,
                    "verification": "unverified",
                    "letter": letter,
                    "clause_id": clause_id,
                })

    return records


def resolve_point_id(tx, record):
    """
    Resolve an exact point ID first.

    For letter 'đ', accept the legacy '?' ID only if
    exactly one matching point exists under its clause
    and no exact Unicode ID exists.
    """
    expected = record["id"]

    result = tx.run(
        """
        MATCH (n:LegalEntity {id: $id})
        RETURN n.id AS id, n.type AS type
        """,
        id=expected,
    ).data()

    if result:
        return expected

    if record.get("letter") != "đ":
        return expected

    legacy_id = record["clause_id"] + "_point_?"

    legacy = tx.run(
        """
        MATCH (c:LegalEntity {id: $clause_id})
              -[r:LEGAL_RELATION]->
              (p:LegalEntity {id: $legacy_id})
        WHERE r.relation = 'HAS_POINT'
        RETURN p.id AS id, p.type AS type
        """,
        clause_id=record["clause_id"],
        legacy_id=legacy_id,
    ).data()

    if len(legacy) == 1 and legacy[0]["type"] == "LegalPoint":
        return legacy_id

    return expected


def inspect_record(tx, record):
    node_id = (
        resolve_point_id(tx, record)
        if record["type"] == "LegalPoint"
        else record["id"]
    )

    matches = tx.run(
        """
        MATCH (n:LegalEntity {id: $id})
        RETURN n.type AS type,
               n.ocr_content AS content
        """,
        id=node_id,
    ).data()

    if len(matches) == 0:
        return "MISSING", node_id

    if len(matches) != 1:
        return "AMBIGUOUS", node_id

    node = matches[0]

    if node["type"] != record["type"]:
        return "WRONG_TYPE", node_id

    if node["content"] is not None:
        return "ALREADY_POPULATED", node_id

    if not str(record["text"]).strip():
        return "EMPTY_TEXT", node_id

    return "ELIGIBLE", node_id


def update_record(tx, node_id, record):
    result = tx.run(
        """
        MATCH (n:LegalEntity {id: $id})
        WHERE n.type = $type
          AND n.ocr_content IS NULL
        SET n.ocr_content = $content,
            n.ocr_source_file = $source_file,
            n.ocr_verification_status = $verification
        RETURN count(n) AS updated
        """,
        id=node_id,
        type=record["type"],
        content=record["text"],
        source_file=record["source_file"],
        verification=record["verification"],
    ).single()

    return result["updated"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--article", type=int)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    records = load_records(args.article)

    print("=== EUREKA CLAUSE/POINT SYNC ===")
    print("Mode:", "APPLY" if args.apply else "DRY-RUN")
    print("Selected records:", len(records))

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(
            os.getenv("NEO4J_USER", "neo4j"),
            os.environ["NEO4J_PASSWORD"],
        ),
    )

    try:
        driver.verify_connectivity()

        with driver.session(database="neo4j") as session:
            inspected = []
            counts = {}

            for record in records:
                status, resolved_id = session.execute_read(
                    inspect_record, record
                )
                inspected.append((record, status, resolved_id))
                counts[status] = counts.get(status, 0) + 1

            for status in sorted(counts):
                print(f"{status}: {counts[status]}")

            problems = [
                (status, node_id)
                for _, status, node_id in inspected
                if status in (
                    "MISSING", "AMBIGUOUS",
                    "WRONG_TYPE", "EMPTY_TEXT"
                )
            ]

            for status, node_id in problems[:30]:
                print(f"PROBLEM {status}: {node_id}")

            eligible = [
                (record, node_id)
                for record, status, node_id in inspected
                if status == "ELIGIBLE"
            ]

            resolved_ids = [node_id for _, node_id in eligible]

            if len(resolved_ids) != len(set(resolved_ids)):
                print("ERROR: Duplicate resolved target IDs.")
                sys.exit(1)

            if problems:
                print("ABORTED: Resolve problems before applying.")
                sys.exit(1)

            if not args.apply:
                print("DRY-RUN COMPLETE. No data modified.")
                return

            updated = 0

            for record, node_id in eligible:
                updated += session.execute_write(
                    update_record, node_id, record
                )

            print("UPDATED:", updated)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
