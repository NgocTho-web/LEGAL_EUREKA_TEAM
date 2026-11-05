import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT_DIR / "data" / "json" / "global_legal_kg_stage2.json"
)

OUTPUT_FILE = (
    ROOT_DIR / "data" / "json" / "global_kg_validation_report.json"
)

# ID trong tài liệu validation -> ID trong SVG
NODE_MAPPING = {
    "vn:law:2013:45-2013-qh13":
        "vn_law_2013_45_2013_qh13",

    "vn:law:2013:45-2013-qh13:article-188":
        "vn_law_2013_45_2013_qh13_article_188",

    "vn:law:2013:45-2013-qh13:article-188:clause-1":
        "vn_law_2013_45_2013_qh13_article_188_clause_1",

    "subject:nguoi_su_dung_dat":
        "subject_nguoi_su_dung_dat",

    "concept:quyen_su_dung_dat":
        "concept_quyen_su_dung_dat",

    "concept:chuyen_nhuong_quyen_su_dung_dat":
        "concept_chuyen_nhuong_quyen_su_dung_dat",

    "concept:giay_chung_nhan_quyen_su_dung_dat":
        "concept_giay_chung_nhan_quyen_su_dung_dat",

    "cond:co_giay_chung_nhan_qsd_dat":
        "cond_co_giay_chung_nhan_qsd_dat",

    "cond:dat_khong_co_tranh_chap":
        "cond_dat_khong_co_tranh_chap",

    "cond:quyen_su_dung_dat_khong_bi_ke_bien":
        "cond_quyen_su_dung_dat_khong_bi_ke_bien",

    "cond:trong_thoi_han_su_dung_dat":
        "cond_trong_thoi_han_su_dung_dat",

    "proc:chuyen_nhuong_quyen_su_dung_dat":
        "proc_chuyen_nhuong_quyen_su_dung_dat",

    "proc:dang_ky_bien_dong_dat_dai":
        "proc_dang_ky_bien_dong_dat_dai",
}

# Các cạnh lấy từ tài liệu validation
# (source trong ID validation, target trong ID validation, relation)
EXPECTED_EDGES = [
    (
        "vn:law:2013:45-2013-qh13",
        "vn:law:2013:45-2013-qh13:article-188",
        "CONTAINS"
    ),
    (
        "vn:law:2013:45-2013-qh13:article-188",
        "vn:law:2013:45-2013-qh13:article-188:clause-1",
        "CONTAINS"
    ),
    (
        "vn:law:2013:45-2013-qh13:article-188:clause-1",
        "subject:nguoi_su_dung_dat",
        "APPLIES_TO"
    ),
    (
        "vn:law:2013:45-2013-qh13:article-188",
        "concept:quyen_su_dung_dat",
        "REGULATES"
    ),
    (
        "vn:law:2013:45-2013-qh13:article-188:clause-1",
        "concept:quyen_su_dung_dat",
        "REGULATES"
    ),
    (
        "vn:law:2013:45-2013-qh13:article-188:clause-1",
        "concept:chuyen_nhuong_quyen_su_dung_dat",
        "REGULATES"
    ),
    (
        "concept:quyen_su_dung_dat",
        "concept:giay_chung_nhan_quyen_su_dung_dat",
        "REGULATES"
    ),
    (
        "concept:quyen_su_dung_dat",
        "cond:co_giay_chung_nhan_qsd_dat",
        "HAS_CONDITION"
    ),
    (
        "concept:quyen_su_dung_dat",
        "cond:dat_khong_co_tranh_chap",
        "HAS_CONDITION"
    ),
    (
        "concept:quyen_su_dung_dat",
        "cond:quyen_su_dung_dat_khong_bi_ke_bien",
        "HAS_CONDITION"
    ),
    (
        "concept:quyen_su_dung_dat",
        "cond:trong_thoi_han_su_dung_dat",
        "HAS_CONDITION"
    ),
    (
        "concept:giay_chung_nhan_quyen_su_dung_dat",
        "cond:co_giay_chung_nhan_qsd_dat",
        "HAS_CONDITION"
    ),
    (
        "concept:chuyen_nhuong_quyen_su_dung_dat",
        "cond:co_giay_chung_nhan_qsd_dat",
        "HAS_CONDITION"
    ),
    (
        "concept:chuyen_nhuong_quyen_su_dung_dat",
        "cond:trong_thoi_han_su_dung_dat",
        "HAS_CONDITION"
    ),
    (
        "concept:chuyen_nhuong_quyen_su_dung_dat",
        "proc:chuyen_nhuong_quyen_su_dung_dat",
        "HAS_PROCEDURE"
    ),
    (
        "concept:chuyen_nhuong_quyen_su_dung_dat",
        "proc:dang_ky_bien_dong_dat_dai",
        "HAS_PROCEDURE"
    ),
]


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        kg = json.load(f)

    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])

    node_map = {
        node["id"]: node
        for node in nodes
        if node.get("id")
    }

    edge_pairs = {
        (edge.get("source"), edge.get("target"))
        for edge in edges
    }

    # Kiểm tra node
    node_results = []

    for validation_id, svg_id in NODE_MAPPING.items():
        exists = svg_id in node_map

        node_results.append({
            "validation_id": validation_id,
            "svg_id": svg_id,
            "exists_in_svg": exists,
            "name": node_map.get(svg_id, {}).get("name"),
            "inferred_type": node_map.get(svg_id, {}).get(
                "inferred_type"
            )
        })

    # Kiểm tra cạnh
    edge_results = []

    for source_id, target_id, relation in EXPECTED_EDGES:
        source = NODE_MAPPING[source_id]
        target = NODE_MAPPING[target_id]

        source_exists = source in node_map
        target_exists = target in node_map
        edge_exists = (source, target) in edge_pairs

        edge_results.append({
            "source": source,
            "target": target,
            "expected_relation": relation,
            "source_exists": source_exists,
            "target_exists": target_exists,
            "edge_exists_in_svg": edge_exists,
            "validation_status": (
                "MATCH"
                if source_exists and target_exists and edge_exists
                else "NOT_MATCH"
            )
        })

    matched_nodes = sum(
        item["exists_in_svg"] for item in node_results
    )

    matched_edges = sum(
        item["validation_status"] == "MATCH"
        for item in edge_results
    )

    report = {
        "summary": {
            "expected_nodes": len(NODE_MAPPING),
            "matched_nodes": matched_nodes,
            "missing_nodes": len(NODE_MAPPING) - matched_nodes,
            "expected_edges": len(EXPECTED_EDGES),
            "matched_edges": matched_edges,
            "missing_edges": len(EXPECTED_EDGES) - matched_edges
        },
        "nodes": node_results,
        "edges": edge_results
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("========== VALIDATION ==========")
    print(
        f"Node khớp: {matched_nodes}/{len(NODE_MAPPING)}"
    )
    print(
        f"Node thiếu: {len(NODE_MAPPING) - matched_nodes}"
    )
    print(
        f"Edge khớp: {matched_edges}/{len(EXPECTED_EDGES)}"
    )
    print(
        f"Edge thiếu: {len(EXPECTED_EDGES) - matched_edges}"
    )

    print("\n===== NODE KHÔNG TÌM THẤY =====")

    for item in node_results:
        if not item["exists_in_svg"]:
            print(item["svg_id"])

    print("\n===== EDGE KHÔNG KHỚP =====")

    for item in edge_results:
        if item["validation_status"] != "MATCH":
            print(
                item["source"],
                "->",
                item["target"],
                "|",
                item["expected_relation"],
                "| source:", item["source_exists"],
                "| target:", item["target_exists"],
                "| edge:", item["edge_exists_in_svg"]
            )

    print("\nĐã lưu báo cáo:", OUTPUT_FILE)


if __name__ == "__main__":
    main()