import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT_DIR / "data" / "json" / "global_legal_kg_stage2.json"
)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    kg = json.load(f)

nodes = kg.get("nodes", [])
edges = kg.get("edges", [])

# Những từ khóa cần tìm
KEYWORDS = [
    "quyền sử dụng đất",
    "giấy chứng nhận",
    "chuyển nhượng",
    "điều 188",
    "article_188"
]

print("========== TÌM NODE THEO TỪ KHÓA ==========")

for keyword in KEYWORDS:
    print(f"\n--- Từ khóa: {keyword} ---")

    found = 0

    for node in nodes:
        node_id = str(node.get("id", ""))
        name = str(node.get("name", ""))

        if (
            keyword.lower() in node_id.lower()
            or keyword.lower() in name.lower()
        ):
            print({
                "id": node_id,
                "name": name,
                "type": node.get("inferred_type")
            })
            found += 1

    print("Số node tìm thấy:", found)


# Tìm node Điều 188
article_188_ids = [
    node["id"]
    for node in nodes
    if "article_188" in node.get("id", "")
]

print("\n========== CÁC NODE ĐIỀU 188 ==========")

for node_id in article_188_ids:
    node = next(n for n in nodes if n["id"] == node_id)

    print("\nNODE:", node_id)
    print("NAME:", node.get("name"))

    print("\nCác cạnh đi ra:")

    for edge in edges:
        if edge.get("source") == node_id:
            target = next(
                (n for n in nodes if n["id"] == edge.get("target")),
                {}
            )

            print(
                "->",
                edge.get("target"),
                "|",
                target.get("name"),
                "|",
                edge.get("relation")
            )

    print("\nCác cạnh đi vào:")

    for edge in edges:
        if edge.get("target") == node_id:
            source = next(
                (n for n in nodes if n["id"] == edge.get("source")),
                {}
            )

            print(
                "<-",
                edge.get("source"),
                "|",
                source.get("name"),
                "|",
                edge.get("relation")
            )