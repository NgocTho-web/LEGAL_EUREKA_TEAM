
import json
from pathlib import Path
from collections import Counter

BASE = Path("data/documents/processed")
AUDIT = BASE / "clause_audit_v3.json"
OUTPUT = BASE / "clause_v3_remaining_issues.txt"


def main():
    with AUDIT.open(encoding="utf-8") as f:
        audit = json.load(f)

    problematic = [
        a for a in audit["articles"]
        if a["issues"]
    ]

    issue_counts = Counter(
        issue.split("_clause_")[0]
        for article in problematic
        for issue in article["issues"]
    )

    lines = [
        "CLAUSE PARSER V3 - REMAINING ISSUES",
        "=" * 65,
        f"Articles with issues: {len(problematic)}",
        "",
        "ISSUE COUNTS:"
    ]

    for issue, count in issue_counts.most_common():
        lines.append(f"  {issue}: {count}")

    lines.extend(["", "DETAILS:", "=" * 65])

    for article in problematic:
        number = article["article_number"]

        lines.append(f"\nDIEU {number}")
        lines.append(
            f"Khoan: {article['clause_numbers']}"
        )
        lines.append(
            f"So diem: {article['point_count']}"
        )

        for issue in article["issues"]:
            lines.append(f"  - {issue}")

    OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print("\n".join(lines))
    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
