import json
from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parents[1]

REPORT_FILE = (
    ROOT_DIR / "data" / "json" / "global_kg_audit_report.json"
)
NORMALIZED_FILE = (
    ROOT_DIR / "data" / "json" / "global_legal_kg_normalized.json"
)

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    report = json.load(f)

with open(NORMALIZED_FILE, "r", encoding="utf-8") as f:
    kg = json.load(f)

node_map = {
    node["id"]: node
    for node in kg["nodes"]
}

candidates = report["structural_candidates"]

# Thống kê loại node nguồn và đích
type_pairs = Counter()

for edge in candidates:
    source_node = node_map.get(edge["source"], {})
    target_node = node_map.get(edge["target"], {})

    source_type = source_node.get("inferred_type", "UNKNOWN")
    target_type = target_node.get("inferred_type", "UNKNOWN")

    type_pairs[(source_type, target_type)] += 1

print("===== THỐNG KÊ CẶP LOẠI NODE =====")

for pair, count in type_pairs.items():
    print(f"{pair[0]} -> {pair[1]}: {count}")

print("\n===== 30 CẠNH CẤU TRÚC ĐẦU TIÊN =====")

for index, edge in enumerate(candidates[:30], start=1):
    source = node_map.get(edge["source"], {})
    target = node_map.get(edge["target"], {})

    print(f"\n{index}.")
    print("SOURCE:", edge["source"])
    print("SOURCE TYPE:", source.get("inferred_type"))
    print("TARGET:", edge["target"])
    print("TARGET TYPE:", target.get("inferred_type"))

print("\n===== MỘT SỐ NODE PHÁP LÝ =====")

for node in kg["nodes"]:
    node_type = node.get("inferred_type")

    if node_type in [
        "LegalSubject",
        "LegalConcept",
        "LegalCondition",
        "LegalProcedure"
    ]:
        print(
            node.get("id"),
            "|",
            node_type,
            "|",
            node.get("label")
        )