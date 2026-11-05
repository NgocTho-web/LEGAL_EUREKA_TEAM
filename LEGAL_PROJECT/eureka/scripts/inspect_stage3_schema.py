
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
KG_PATH = ROOT / "data" / "json" / "global_legal_kg_stage3.json"

with KG_PATH.open("r", encoding="utf-8") as f:
    kg = json.load(f)

print("=" * 65)
print("EUREKA - STAGE 3 SCHEMA INSPECTION")
print("=" * 65)

print("\nROOT TYPE:", type(kg).__name__)

if isinstance(kg, dict):
    print("ROOT KEYS:", list(kg.keys()))

    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])

elif isinstance(kg, list):
    nodes = kg
    edges = []

else:
    raise TypeError("Unsupported KG root structure")

print("\nTOTAL NODES:", len(nodes))
print("TOTAL EDGES:", len(edges))

if nodes:
    print("\n--- NODE FIELD COUNTS ---")
    node_fields = Counter(
        key for node in nodes if isinstance(node, dict)
        for key in node.keys()
    )

    for key, count in node_fields.most_common():
        print(f"{key}: {count}/{len(nodes)}")

    print("\n--- SAMPLE NODES ---")
    for node in nodes[:3]:
        print(json.dumps(
            node,
            ensure_ascii=False,
            indent=2
        ))

if edges:
    print("\n--- EDGE FIELD COUNTS ---")
    edge_fields = Counter(
        key for edge in edges if isinstance(edge, dict)
        for key in edge.keys()
    )

    for key, count in edge_fields.most_common():
        print(f"{key}: {count}/{len(edges)}")

    print("\n--- SAMPLE EDGES ---")
    for edge in edges[:5]:
        print(json.dumps(
            edge,
            ensure_ascii=False,
            indent=2
        ))
