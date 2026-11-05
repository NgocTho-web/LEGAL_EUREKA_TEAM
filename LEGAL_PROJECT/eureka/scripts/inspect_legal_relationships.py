import json
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT_DIR / "data" / "json" / "global_legal_kg_stage2.json"
)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    kg = json.load(f)

nodes = kg["nodes"]
edges = kg["edges"]

node_map = {
    node["id"]: node
    for node in nodes
}

# Tạo chỉ mục cạnh vào và cạnh ra
outgoing = defaultdict(list)
incoming = defaultdict(list)

for edge in edges:
    outgoing[edge["source"]].append(edge)
    incoming[edge["target"]].append(edge)


def show_node(node_id):
    node = node_map.get(node_id)

    if not node:
        print("\nKhông tìm thấy:", node_id)
        return

    print("\n" + "=" * 65)
    print("NODE:", node.get("name"))
    print("ID:", node_id)
    print("TYPE:", node.get("inferred_type"))

    print("\n--- CẠNH ĐI RA ---")

    for edge in outgoing[node_id]:
        target = node_map.get(edge["target"], {})

        print(
            node.get("name"),
            "->",
            target.get("name"),
            "|",
            edge.get("relation")
        )

    print("\n--- CẠNH ĐI VÀO ---")

    for edge in incoming[node_id]:
        source = node_map.get(edge["source"], {})

        print(
            source.get("name"),
            "->",
            node.get("name"),
            "|",
            edge.get("relation")
        )


# Các node cần kiểm tra
target_ids = [
    "concept_chuyen_nhuong_quyen_su_dung_dat",
    "concept_gop_von_bang_quyen_su_dung_dat",
    "concept_the_chap_quyen_su_dung_dat",
    "cond_co_giay_chung_nhan_qsd_dat",
    "cond_dat_khong_co_tranh_chap",
    "cond_quyen_su_dung_dat_khong_bi_ke_bien",
    "cond_trong_thoi_han_su_dung_dat",
    "proc_chuyen_nhuong_quyen_su_dung_dat",
    "proc_dang_ky_bien_dong_dat_dai",
]

for node_id in target_ids:
    show_node(node_id)