
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FILE = BASE_DIR / "data/json/global_legal_kg_stage3.json"

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

nodes = {node["id"]: node for node in data["nodes"]}

ARTICLE_ID = "vn_law_2013_45_2013_qh13_article_188"
CONCEPT_ID = "concept_chuyen_nhuong_quyen_su_dung_dat"

def node_name(node_id):
    node = nodes.get(node_id)
    return node.get("name", node_id) if node else node_id

def relation(edge):
    return (
        edge.get("inferred_relation")
        or edge.get("relation")
        or "UNKNOWN"
    )

def show_edge(edge):
    print(
        f'{node_name(edge["source"])} '
        f'[{edge["source"]}]'
        f' --{relation(edge)}--> '
        f'{node_name(edge["target"])} '
        f'[{edge["target"]}]'
    )

print("\n===== ĐIỀU 188 =====")

if ARTICLE_ID not in nodes:
    print("Không tìm thấy Điều 188!")
    raise SystemExit(1)

print("ID:", ARTICLE_ID)
print("Tên:", node_name(ARTICLE_ID))

article_edges = [
    e for e in data["edges"]
    if e["source"] == ARTICLE_ID or e["target"] == ARTICLE_ID
]

for edge in article_edges:
    show_edge(edge)

print("\n===== CÁC KHOẢN THUỘC ĐIỀU 188 =====")

clause_ids = []

for edge in data["edges"]:
    if (
        edge["source"] == ARTICLE_ID
        and nodes.get(edge["target"], {}).get("inferred_type") == "Clause"
    ):
        clause_ids.append(edge["target"])
        show_edge(edge)

print("\n===== CÁC KHOẢN LIÊN KẾT VỚI CHUYỂN NHƯỢNG =====")

for clause_id in clause_ids:
    for edge in data["edges"]:
        if (
            edge["source"] == clause_id
            and edge["target"] == CONCEPT_ID
        ):
            show_edge(edge)

print("\n===== ĐIỀU KIỆN VÀ THỦ TỤC CỦA CHUYỂN NHƯỢNG =====")

for edge in data["edges"]:
    if edge["source"] == CONCEPT_ID:
        show_edge(edge)

print("\n===== KẾT THÚC KIỂM TRA =====")
