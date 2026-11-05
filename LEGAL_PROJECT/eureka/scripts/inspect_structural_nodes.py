
import json
from pathlib import Path

# Đọc file Knowledge Graph
PROJECT_ROOT = Path(__file__).resolve().parent.parent
path = PROJECT_ROOT / "data" / "json" / "global_legal_kg_stage3.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Khai báo danh sách nodes trước khi sử dụng
nodes = data.get("nodes", [])

print("=" * 70)
print(f"TỔNG SỐ NODE: {len(nodes)}")

# Kiểm tra các trường nội dung
content_fields = [
    "content",
    "content_text",
    "text",
    "body",
    "full_text",
]

print("\n" + "=" * 70)
print("THỐNG KÊ TRƯỜNG NỘI DUNG")

for field in content_fields:
    count = sum(
        1
        for node in nodes
        if isinstance(node.get(field), str)
        and node.get(field).strip()
    )
    print(f"{field}: {count}/{len(nodes)} node")

# Kiểm tra một số node cấu trúc
target_ids = [
    "vn_law_2013_45_2013_qh13_article_188",
    "vn_law_2013_45_2013_qh13_article_188_clause_1",
    "vn_law_2013_45_2013_qh13_article_149_clause_5",
]

node_index = {
    node.get("id"): node
    for node in nodes
    if node.get("id")
}

for node_id in target_ids:
    print("\n" + "=" * 70)
    print("NODE ID:", node_id)

    node = node_index.get(node_id)

    if node:
        print(json.dumps(node, ensure_ascii=False, indent=2))
    else:
        print("KHÔNG TÌM THẤY NODE")
