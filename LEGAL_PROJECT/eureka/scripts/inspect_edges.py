
import json
from pathlib import Path

path = Path("data/json/global_legal_kg_stage3.json")

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

count = 0

for edge in data.get("edges", []):
    relation = edge.get("relation")
    inferred = edge.get("inferred_relation")

    if relation == "REGULATES" or inferred == "REGULATES":
        print(f"\n===== EDGE {count + 1} =====")
        print(json.dumps(edge, ensure_ascii=False, indent=2))

        count += 1
        if count == 3:
            break

if count == 0:
    print("Không tìm thấy cạnh REGULATES.")
