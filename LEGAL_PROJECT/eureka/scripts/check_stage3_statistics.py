
import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[1]
FILE = BASE_DIR / "data/json/global_legal_kg_stage3.json"

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Chuẩn hóa giá trị rỗng
def get_relation(edge):
    return (
        edge.get("inferred_relation")
        or edge.get("relation")
        or "UNKNOWN"
    )


print("\n===== PHÂN BỐ LOẠI NODE =====")

node_types = Counter(
    node.get("inferred_type") or "UNKNOWN"
    for node in data["nodes"]
)

for node_type, count in sorted(node_types.items()):
    print(f"{node_type}: {count}")


print("\n===== PHÂN BỐ QUAN HỆ =====")

relations = Counter(
    get_relation(edge)
    for edge in data["edges"]
)

for relation, count in sorted(relations.items()):
    print(f"{relation}: {count}")


print("\n===== CÁC CẠNH ARTICLE/CLAUSE/CHAPTER/SECTION -> LEGALCONCEPT =====")

nodes = {
    node["id"]: node
    for node in data["nodes"]
}

count = 0

structural_types = {
    "Article",
    "Clause",
    "Chapter",
    "Section",
    "Component"
}

for edge in data["edges"]:
    source = nodes.get(edge.get("source"), {})
    target = nodes.get(edge.get("target"), {})

    source_type = source.get("inferred_type")
    target_type = target.get("inferred_type")

    if (
        source_type in structural_types
        and target_type == "LegalConcept"
    ):
        print(
            source.get("name", edge["source"]),
            "->",
            target.get("name", edge["target"]),
            "|",
            get_relation(edge)
        )
        count += 1

print("\nTổng cạnh cấu trúc -> LegalConcept:", count)


print("\n===== KIỂM TRA CẠNH THIẾU NODE ĐẦU MÚT =====")

missing = []

for edge in data["edges"]:
    if (
        edge.get("source") not in nodes
        or edge.get("target") not in nodes
    ):
        missing.append(edge)

print("Số cạnh thiếu node đầu mút:", len(missing))
