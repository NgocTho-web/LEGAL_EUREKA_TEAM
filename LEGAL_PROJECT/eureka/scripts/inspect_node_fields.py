import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT_DIR / "data" / "json" / "global_legal_kg_stage2.json"
)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    kg = json.load(f)

print("===== CẤU TRÚC NODE =====")

for node in kg.get("nodes", [])[:5]:
    print(json.dumps(node, ensure_ascii=False, indent=2))

print("\n===== CẤU TRÚC NODE PHÁP LÝ =====")

count = 0

for node in kg.get("nodes", []):
    if node.get("inferred_type") in [
        "LegalSubject",
        "LegalConcept",
        "LegalCondition",
        "LegalProcedure"
    ]:
        print(json.dumps(node, ensure_ascii=False, indent=2))
        count += 1

        if count >= 5:
            break