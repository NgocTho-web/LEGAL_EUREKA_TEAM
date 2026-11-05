
import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]

KG_PATH = (
    PROJECT_ROOT
    / "data"
    / "json"
    / "global_legal_kg_svg_extracted.json"
)

with open(KG_PATH, "r", encoding="utf-8") as f:
    kg = json.load(f)

nodes = kg.get("nodes", [])
edges = kg.get("edges", [])

node_ids = [node.get("id") for node in nodes]
node_id_set = set(node_ids)

# Kiểm tra node trùng ID
duplicates = [
    node_id
    for node_id, count in Counter(node_ids).items()
    if count > 1
]

# Kiểm tra cạnh không có node nguồn hoặc đích
invalid_edges = []

for edge in edges:
    source = edge.get("source")
    target = edge.get("target")

    if source not in node_id_set or target not in node_id_set:
        invalid_edges.append(edge)

# Kiểm tra quan hệ
relation_counts = Counter(
    edge.get("relation", "UNKNOWN")
    for edge in edges
)

print("========== KG INSPECTION ==========")
print("Tổng nodes:", len(nodes))
print("Tổng edges:", len(edges))
print("Node ID trùng:", len(duplicates))
print("Cạnh thiếu node đầu/cuối:", len(invalid_edges))
print("Số loại quan hệ:", len(relation_counts))

print("\nPhân bố quan hệ:")

for relation, count in relation_counts.items():
    print(f"{relation}: {count}")

print("\n10 nodes đầu tiên:")

for node in nodes[:10]:
    print(node)

print("\n10 edges đầu tiên:")

for edge in edges[:10]:
    print(edge)
