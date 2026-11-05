
import json
import re
from pathlib import Path
from collections import Counter

# Đường dẫn dự án
ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT_DIR
    / "data"
    / "json"
    / "global_legal_kg_svg_extracted.json"
)

OUTPUT_FILE = (
    ROOT_DIR
    / "data"
    / "json"
    / "global_legal_kg_normalized.json"
)


def infer_node_type(node_id):
    """
    Phân loại sơ bộ dựa trên cấu trúc ID.
    Không thay đổi type gốc.
    """

    if re.search(r"_article_\d+_clause_\d+", node_id):
        return "Clause"

    if re.search(r"_article_\d+", node_id):
        return "Article"

    if re.search(r"_chapter_\d+_section_\d+", node_id):
        return "Section"

    if re.search(r"_chapter_\d+", node_id):
        return "Chapter"

    if node_id.startswith("subject_"):
        return "LegalSubject"

    if node_id.startswith("concept_"):
        return "LegalConcept"

    if node_id.startswith("cond_"):
        return "LegalCondition"

    if node_id.startswith("proc_"):
        return "LegalProcedure"

    if node_id.startswith("vn_law_"):
        return "Document"

    return "UNKNOWN"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file đầu vào: {INPUT_FILE}"
        )

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    node_ids = [node.get("id") for node in nodes]
    node_id_set = set(node_ids)

    # Kiểm tra ID trùng
    duplicate_ids = [
        node_id
        for node_id, count in Counter(node_ids).items()
        if count > 1
    ]

    # Phân loại sơ bộ, không ghi đè type gốc
    type_counter = Counter()

    for node in nodes:
        inferred_type = infer_node_type(node.get("id", ""))

        node["inferred_type"] = inferred_type
        node["inference_basis"] = "node_id_pattern"

        type_counter[inferred_type] += 1

    # Kiểm tra endpoint của cạnh
    missing_endpoints = []

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if source not in node_id_set:
            missing_endpoints.append(source)

        if target not in node_id_set:
            missing_endpoints.append(target)

    # Giữ nguyên relation UNKNOWN
    relation_counter = Counter(
        edge.get("relation", "UNKNOWN")
        for edge in edges
    )

    # Thêm báo cáo kiểm tra
    data["normalization_report"] = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "duplicate_node_ids": duplicate_ids,
        "missing_endpoints": missing_endpoints,
        "inferred_node_types": dict(type_counter),
        "edge_relations": dict(relation_counter),
        "note": (
            "inferred_type chỉ là phân loại sơ bộ từ ID. "
            "Không thay thế type gốc và không xác minh "
            "ý nghĩa pháp lý của các quan hệ."
        )
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("===== NORMALIZATION RESULT =====")
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    print(f"Duplicate IDs: {len(duplicate_ids)}")
    print(f"Missing endpoints: {len(missing_endpoints)}")

    print("\n===== INFERRED NODE TYPES =====")

    for node_type, count in type_counter.items():
        print(f"{node_type}: {count}")

    print("\n===== EDGE RELATIONS =====")

    for relation, count in relation_counter.items():
        print(f"{relation}: {count}")

    print("\nOutput:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
