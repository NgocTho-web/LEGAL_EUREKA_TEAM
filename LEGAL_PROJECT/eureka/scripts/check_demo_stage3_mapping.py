
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "json"

with (DATA / "global_legal_kg_stage3.json").open(
    "r", encoding="utf-8"
) as f:
    stage3 = json.load(f)

with (DATA / "legal_kg_demo_converted.json").open(
    "r", encoding="utf-8"
) as f:
    demo = json.load(f)


stage3_nodes = {
    node["id"]: node
    for node in stage3["nodes"]
    if node.get("id")
}

stage3_ids = set(stage3_nodes)


def collect_demo_nodes(items, result=None):
    if result is None:
        result = []

    for item in items:
        if not isinstance(item, dict):
            continue

        result.append(item)

        for key in ["chapters", "articles", "clauses", "points"]:
            children = item.get(key, [])
            if isinstance(children, list):
                collect_demo_nodes(children, result)

    return result


demo_nodes = collect_demo_nodes(demo.get("documents", []))

print("=" * 70)
print("DEMO - STAGE 3 ID MAPPING")
print("=" * 70)

matched = 0
unmatched = []

for node in demo_nodes:
    demo_id = node.get("id", "")

    # Chỉ tạo ID ứng viên để kiểm tra, không tự động ghi dữ liệu.
    candidate_id = demo_id.replace(":", "_").replace("-", "_")

    exact = demo_id in stage3_ids
    candidate = candidate_id in stage3_ids

    if exact:
        matched += 1
        status = "EXACT MATCH"
        target_id = demo_id
    elif candidate:
        matched += 1
        status = "CANDIDATE MATCH"
        target_id = candidate_id
    else:
        status = "NO MATCH"
        target_id = None
        unmatched.append(demo_id)

    print({
        "demo_id": demo_id,
        "stage3_id_candidate": candidate_id,
        "status": status,
        "target_id": target_id,
        "name": node.get("name")
    })

print("\nSUMMARY")
print("Total demo nodes:", len(demo_nodes))
print("Matched or candidate:", matched)
print("Unmatched:", len(unmatched))
