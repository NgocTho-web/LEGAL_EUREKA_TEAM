import json
from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT_DIR / "data" / "json" / "global_legal_kg_normalized.json"
)

AUDIT_FILE = (
    ROOT_DIR / "data" / "json" / "global_kg_audit_report.json"
)

OUTPUT_FILE = (
    ROOT_DIR / "data" / "json" / "global_legal_kg_stage2.json"
)


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        kg = json.load(f)

    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        audit = json.load(f)

    # Tạo tập các cạnh cấu trúc đã tìm được
    structural_edges = {
        (edge["source"], edge["target"])
        for edge in audit.get("structural_candidates", [])
    }

    inferred_counter = Counter()
    unknown_count = 0

    # Không ghi đè relation gốc
    for edge in kg.get("edges", []):
        key = (edge.get("source"), edge.get("target"))

        if key in structural_edges:
            edge["inferred_relation"] = "CONTAINS"
            edge["inference_basis"] = "parent_child_id_pattern"
            edge["inference_status"] = "candidate"
            inferred_counter["CONTAINS"] += 1
        else:
            edge["inferred_relation"] = None
            edge["inference_basis"] = None
            edge["inference_status"] = "unclassified"
            unknown_count += 1

    # Lưu báo cáo xử lý
    kg["stage2_report"] = {
        "description": (
            "Structural relation candidates inferred from node ID patterns. "
            "Original relations are preserved."
        ),
        "inferred_relation_distribution": dict(inferred_counter),
        "unclassified_edge_count": unknown_count,
        "total_edge_count": len(kg.get("edges", [])),
        "warning": (
            "CONTAINS values are candidates, not legally verified relations."
        )
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(kg, f, ensure_ascii=False, indent=2)

    print("========== STAGE 2 ==========")
    print("Tổng node:", len(kg.get("nodes", [])))
    print("Tổng edge:", len(kg.get("edges", [])))

    print("\nQuan hệ suy luận:")
    for relation, count in inferred_counter.items():
        print(f"{relation}: {count}")

    print("Cạnh chưa phân loại:", unknown_count)

    # Kiểm tra relation gốc có còn UNKNOWN không
    original_relations = Counter(
        edge.get("relation", "UNKNOWN")
        for edge in kg.get("edges", [])
    )

    print("\nQuan hệ gốc:")
    for relation, count in original_relations.items():
        print(f"{relation}: {count}")

    print("\nĐã tạo:", OUTPUT_FILE)


if __name__ == "__main__":
    main()