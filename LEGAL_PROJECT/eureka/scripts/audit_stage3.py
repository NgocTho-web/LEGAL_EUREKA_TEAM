
import json
from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parents[1]
KG_FILE = ROOT_DIR / "data" / "json" / "global_legal_kg_stage3.json"


def main():
    if not KG_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy KG: {KG_FILE}")

    with KG_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    # Kiểm tra ID node
    node_ids = [node.get("id") for node in nodes]
    valid_ids = [node_id for node_id in node_ids if node_id]

    duplicate_ids = [
        node_id for node_id, count in Counter(valid_ids).items()
        if count > 1
    ]

    node_id_set = set(valid_ids)

    # Thống kê loại node
    node_types = Counter(
        node.get("type") or node.get("inferred_type") or "UNKNOWN"
        for node in nodes
    )

    # Thống kê quan hệ gốc và quan hệ suy luận
    original_relations = Counter(
        edge.get("relation") or "UNKNOWN"
        for edge in edges
    )

    inferred_relations = Counter(
        edge.get("inferred_relation") or "NONE"
        for edge in edges
    )

    inference_status = Counter(
        edge.get("inference_status") or "NONE"
        for edge in edges
    )

    # Kiểm tra cạnh tham chiếu node không tồn tại
    dangling_edges = []

    for index, edge in enumerate(edges):
        source = edge.get("source")
        target = edge.get("target")

        if source not in node_id_set or target not in node_id_set:
            dangling_edges.append({
                "index": index,
                "source": source,
                "target": target,
                "source_exists": source in node_id_set,
                "target_exists": target in node_id_set,
            })

    # Thống kê metadata
    metadata = data.get("metadata", {})

    print("=" * 65)
    print("EUREKA - GLOBAL LEGAL KG STAGE 3 AUDIT")
    print("=" * 65)

    print(f"\nFile: {KG_FILE}")
    print(f"Total nodes: {len(nodes)}")
    print(f"Total edges: {len(edges)}")
    print(f"Unique node IDs: {len(node_id_set)}")
    print(f"Duplicate node IDs: {len(duplicate_ids)}")
    print(f"Dangling edges: {len(dangling_edges)}")

    print("\n--- NODE TYPES ---")
    for key, value in node_types.most_common():
        print(f"{key}: {value}")

    print("\n--- ORIGINAL RELATIONS ---")
    for key, value in original_relations.most_common():
        print(f"{key}: {value}")

    print("\n--- INFERRED RELATIONS ---")
    for key, value in inferred_relations.most_common():
        print(f"{key}: {value}")

    print("\n--- INFERENCE STATUS ---")
    for key, value in inference_status.most_common():
        print(f"{key}: {value}")

    print("\n--- METADATA ---")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))

    print("\n--- SAMPLE NODE ---")
    if nodes:
        print(json.dumps(nodes[0], ensure_ascii=False, indent=2))

    print("\n--- SAMPLE EDGE ---")
    if edges:
        print(json.dumps(edges[0], ensure_ascii=False, indent=2))

    if duplicate_ids:
        print("\n--- DUPLICATE IDS (first 20) ---")
        print(duplicate_ids[:20])

    if dangling_edges:
        print("\n--- DANGLING EDGES (first 20) ---")
        print(json.dumps(dangling_edges[:20], ensure_ascii=False, indent=2))

    # Lưu báo cáo để dùng ở các giai đoạn sau
    report = {
        "file": str(KG_FILE),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "unique_node_ids": len(node_id_set),
        "duplicate_node_ids": duplicate_ids,
        "dangling_edges": dangling_edges,
        "node_types": dict(node_types),
        "original_relations": dict(original_relations),
        "inferred_relations": dict(inferred_relations),
        "inference_status": dict(inference_status),
        "metadata": metadata,
    }

    report_path = ROOT_DIR / "data" / "json" / "global_kg_stage3_audit.json"

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nAudit report saved: {report_path}")


if __name__ == "__main__":
    main()
