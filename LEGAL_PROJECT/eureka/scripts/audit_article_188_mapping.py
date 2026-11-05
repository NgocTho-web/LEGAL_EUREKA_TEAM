
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
KG_PATH = ROOT / "data" / "json" / "global_legal_kg_stage3.json"

with KG_PATH.open("r", encoding="utf-8") as f:
    kg = json.load(f)

nodes = kg["nodes"]
edges = kg["edges"]

node_by_id = {
    node["id"]: node
    for node in nodes
    if node.get("id")
}

print("=" * 70)
print("STAGE 3 - NODE TYPE AUDIT")
print("=" * 70)

type_counts = Counter(
    node.get("inferred_type", "UNKNOWN")
    for node in nodes
)

for node_type, count in type_counts.most_common():
    print(f"{node_type}: {count}")

print("\n" + "=" * 70)
print("ARTICLE 188 NODE")
print("=" * 70)

article_id = "vn_law_2013_45_2013_qh13_article_188"

article = node_by_id.get(article_id)
print(json.dumps(article, ensure_ascii=False, indent=2))

print("\n" + "=" * 70)
print("ARTICLE 188 DESCENDANTS")
print("=" * 70)

visited = set()

def traverse(parent_id, depth=0):
    if parent_id in visited:
        return

    visited.add(parent_id)

    child_edges = [
        edge for edge in edges
        if edge.get("source") == parent_id
    ]

    for edge in child_edges:
        child_id = edge.get("target")
        child = node_by_id.get(child_id)

        if not child:
            continue

        print(
            "  " * depth,
            child.get("name"),
            "|",
            child.get("id"),
            "|",
            child.get("inferred_type"),
            "| relation:",
            edge.get("inferred_relation"),
            "| status:",
            edge.get("inference_status")
        )

        traverse(child_id, depth + 1)


if article:
    traverse(article_id)

print("\n" + "=" * 70)
print("ALL POINT NODES")
print("=" * 70)

point_nodes = [
    node for node in nodes
    if node.get("inferred_type") == "Point"
]

print("TOTAL POINT NODES:", len(point_nodes))

for node in point_nodes[:30]:
    print(node.get("id"), "|", node.get("name"))

print("\nAUDIT COMPLETED")
