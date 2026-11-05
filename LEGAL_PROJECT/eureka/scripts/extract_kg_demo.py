
import json
import re
from pathlib import Path

html_path = Path("visualization/legal_kg_demo.html")
output_path = Path("data/json/legal_kg_demo_extracted.json")

html = html_path.read_text(encoding="utf-8")

def extract_dataset(name):
    pattern = (
        rf"{name}\s*=\s*new\s+vis\.DataSet\((\[.*?\])\);"
    )

    match = re.search(pattern, html, re.DOTALL)

    if not match:
        raise ValueError(f"Không tìm thấy mảng {name} trong HTML")

    return json.loads(match.group(1))

nodes = extract_dataset("nodes")
edges = extract_dataset("edges")

result = {
    "source": "visualization/legal_kg_demo.html",
    "data_type": "demo",
    "nodes": nodes,
    "edges": edges
}

output_path.parent.mkdir(parents=True, exist_ok=True)

output_path.write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("TRICH XUAT THANH CONG")
print("So nodes:", len(nodes))
print("So edges:", len(edges))
print("File:", output_path)
