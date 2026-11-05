
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "json"

FILES = [
    "global_legal_kg_normalized.json",
    "global_legal_kg_stage2.json",
    "global_legal_kg_stage3.json",
    "global_legal_kg_svg_extracted.json",
    "global_legal_kg_stage3.backup.json",
    "legal_kg_demo_converted.json",
    "legal_kg_demo_extracted.json",
    "legal_knowledge_graph.json",
]

CONTENT_FIELDS = [
    "content", "text", "description", "body",
    "full_text", "article_content", "paragraph",
    "title", "name", "label"
]


def inspect_file(filename):
    path = DATA_DIR / filename

    print("\n" + "=" * 75)
    print("FILE:", filename)
    print("=" * 75)

    if not path.exists():
        print("FILE NOT FOUND")
        return

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print("READ ERROR:", exc)
        return

    print("ROOT TYPE:", type(data).__name__)

    if isinstance(data, dict):
        print("ROOT KEYS:", list(data.keys()))
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
    elif isinstance(data, list):
        nodes = data
        edges = []
    else:
        print("Unsupported root structure")
        return

    print("NODES:", len(nodes) if isinstance(nodes, list) else "N/A")
    print("EDGES:", len(edges) if isinstance(edges, list) else "N/A")

    if not isinstance(nodes, list) or not nodes:
        print("No node list found.")
        return

    fields = Counter(
        key
        for node in nodes
        if isinstance(node, dict)
        for key in node.keys()
    )

    print("\nNODE FIELDS:")
    for key, count in fields.most_common():
        print(f"  {key}: {count}/{len(nodes)}")

    print("\nCONTENT FIELD COUNTS:")
    for field in CONTENT_FIELDS:
        count = sum(
            1 for node in nodes
            if isinstance(node, dict)
            and node.get(field) not in (None, "")
        )
        print(f"  {field}: {count}/{len(nodes)}")

    print("\nSAMPLE NODES:")
    for node in nodes[:2]:
        print(json.dumps(
            node,
            ensure_ascii=False,
            indent=2
        ))


def main():
    for filename in FILES:
        inspect_file(filename)


if __name__ == "__main__":
    main()
