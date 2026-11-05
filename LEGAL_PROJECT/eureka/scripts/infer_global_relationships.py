
import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "data/json/global_legal_kg_stage2.json"
OUTPUT_FILE = BASE_DIR / "data/json/global_legal_kg_stage3.json"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = {
        node["id"]: node
        for node in data["nodes"]
    }

    stats = Counter()

    for edge in data["edges"]:
        source = nodes.get(edge.get("source"))
        target = nodes.get(edge.get("target"))

        if not source or not target:
            continue

        source_type = source.get("inferred_type")
        target_type = target.get("inferred_type")


        inferred_relation = None
        basis = None

        # LegalConcept -> LegalCondition
        if (
            source_type == "LegalConcept"
            and target_type == "LegalCondition"
        ):
            inferred_relation = "HAS_CONDITION"
            basis = "concept_to_condition"

        # LegalConcept -> LegalProcedure
        elif (
            source_type == "LegalConcept"
            and target_type == "LegalProcedure"
        ):
            inferred_relation = "HAS_PROCEDURE"
            basis = "concept_to_procedure"

        # LegalConcept -> LegalSubject
        elif (
            source_type == "LegalConcept"
            and target_type == "LegalSubject"
        ):
            inferred_relation = "APPLIES_TO"
            basis = "concept_to_subject"

        # Article / Clause / Chapter / Section -> LegalConcept
        elif (
            source_type in {
                "Article",
                "Clause",
                "Chapter",
                "Section"
            }
            and target_type == "LegalConcept"
        ):
            inferred_relation = "REGULATES"
            basis = "structural_component_to_concept"


        if inferred_relation:
            edge["inferred_relation"] = inferred_relation
            edge["inference_basis"] = basis
            edge["inference_status"] = "candidate"
            stats[inferred_relation] += 1

    data.setdefault("metadata", {})
    data["metadata"]["relationship_inference"] = {
        "method": "node_type_based",
        "status": "candidate_not_source_verified"
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Đã tạo:", OUTPUT_FILE)
    print("Thống kê quan hệ suy luận:")

    for relation, count in stats.items():
        print(f"{relation}: {count}")

    print("Tổng cạnh:", len(data["edges"]))


if __name__ == "__main__":
    main()
