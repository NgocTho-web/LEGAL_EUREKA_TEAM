
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "json"

FILES = [
    "legal_kg_demo_converted.json",
    "legal_knowledge_graph.json",
]

for filename in FILES:
    path = DATA_DIR / filename

    print("\n" + "=" * 70)
    print("FILE:", filename)
    print("=" * 70)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for key, value in data.items():
        print(f"\nKEY: {key}")
        print("TYPE:", type(value).__name__)

        if isinstance(value, list):
            print("COUNT:", len(value))

            for item in value[:3]:
                print(json.dumps(
                    item,
                    ensure_ascii=False,
                    indent=2
                ))

        elif isinstance(value, dict):
            print(json.dumps(
                value,
                ensure_ascii=False,
                indent=2
            )[:3000])

        else:
            print(value)
