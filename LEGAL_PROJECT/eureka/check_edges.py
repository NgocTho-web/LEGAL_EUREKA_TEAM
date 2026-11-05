import json
from pathlib import Path

path = Path("data/json/global_legal_kg_stage3.json")

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

target_ids = [
    "vn_law_2013_45_2013_qh13_article_188",
    "vn_law_2013_45_2013_qh13_article_188_clause_1"
]

print("CẤU TRÚC NODE ĐIỀU 188 VÀ KHOẢN 1")

for node in data.get("nodes", []):
    if node.get("id") in target_ids:
        print("\n" + "=" * 60)
        print(json.dumps(node, ensure_ascii=False, indent=2))