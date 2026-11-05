
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG_PATH = ROOT / "data" / "json" / "global_legal_kg_stage3.json"

with KG_PATH.open("r", encoding="utf-8") as f:
    kg = json.load(f)

nodes = kg.get("nodes", [])

print("TOTAL NODES:", len(nodes))

content_fields = [
    "content",
    "text",
    "description",
    "body",
    "title",
    "name",
    "label"
]

for field in content_fields:
    count = sum(
        1 for node in nodes
        if isinstance(node, dict)
        and node.get(field) not in (None, "")
    )
    print(f"{field}: {count}")

print("\n--- NODES WITH CONTENT ---")

shown = 0

for node in nodes:
    if not isinstance(node, dict):
        continue

    values = {
        field: node.get(field)
        for field in content_fields
        if node.get(field) not in (None, "")
    }

    if values:
        print(json.dumps(
            {
                "id": node.get("id"),
                "type": node.get("type"),
                "inferred_type": node.get("inferred_type"),
                "values": values
            },
            ensure_ascii=False,
            indent=2
        ))

        shown += 1

    if shown >= 5:
        break
