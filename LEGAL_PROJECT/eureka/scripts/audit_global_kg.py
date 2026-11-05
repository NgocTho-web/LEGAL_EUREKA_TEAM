import json
from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT_DIR / "data" / "json" / "global_legal_kg_normalized.json"
OUTPUT_FILE = ROOT_DIR / "data" / "json" / "global_kg_audit_report.json"


def get_parent_candidate(node_id):
    """
    Chỉ tìm node cha theo cấu trúc ID.
    Không tự kết luận quan hệ pháp lý.
    """

    suffixes = [
        "_clause_",
        "_section_",
        "_article_",
        "_chapter_",
    ]

    # Clause -> Article
    if "_article_" in node_id and "_clause_" in node_id:
        return node_id.rsplit("_clause_", 1)[0]

    # Section -> Chapter
    if "_chapter_" in node_id and "_section_" in node_id:
        return node_id.rsplit("_section_", 1)[0]

    # Article -> Chapter
    if "_chapter_" in node_id and "_article_" in node_id:
        return node_id.rsplit("_article_", 1)[0]

    # Chapter -> Document
    if "_chapter_" in node_id:
        return node_id.rsplit("_chapter_", 1)[0]

    return None


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file: {INPUT_FILE}"
        )

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    node_ids = {
        node.get("id")
        for node in nodes
        if node.get("id")
    }

    # 1. Thống kê loại node
    type_counter = Counter(
        node.get("inferred_type", "UNKNOWN")
        for node in nodes
    )

    # 2. Thống kê quan hệ cạnh
    relation_counter = Counter(
        edge.get("relation", "UNKNOWN")
        for edge in edges
    )

    # 3. Kiểm tra các cạnh có endpoint hợp lệ
    invalid_edges = []

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if source not in node_ids or target not in node_ids:
            invalid_edges.append(edge)

    # 4. Tìm các cạnh có khả năng là quan hệ cấu trúc
    structural_candidates = []

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if not source or not target:
            continue

        parent_candidate = get_parent_candidate(target)

        if parent_candidate and source == parent_candidate:
            structural_candidates.append({
                "source": source,
                "target": target,
                "candidate_relation": "CONTAINS",
                "original_relation": edge.get("relation", "UNKNOWN"),
                "basis": "parent_child_id_pattern",
                "verified": False
            })

    # 5. Tổng hợp báo cáo
    report = {
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_type_distribution": dict(type_counter),
            "edge_relation_distribution": dict(relation_counter),
            "invalid_edge_count": len(invalid_edges),
            "structural_candidate_count": len(structural_candidates)
        },
        "invalid_edges": invalid_edges,
        "structural_candidates": structural_candidates
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("========== KG AUDIT ==========")
    print(f"Tổng node: {len(nodes)}")
    print(f"Tổng edge: {len(edges)}")

    print("\nPhân bố loại node:")
    for node_type, count in type_counter.items():
        print(f"  {node_type}: {count}")

    print("\nPhân bố loại quan hệ:")
    for relation, count in relation_counter.items():
        print(f"  {relation}: {count}")

    print(f"\nCạnh không hợp lệ: {len(invalid_edges)}")
    print(f"Cạnh cấu trúc có thể xác minh: {len(structural_candidates)}")

    print(f"\nĐã lưu báo cáo tại: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()