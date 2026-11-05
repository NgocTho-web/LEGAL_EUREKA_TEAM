
import json
import re
from pathlib import Path


INPUT_PATH = Path("data/json/legal_kg_demo_extracted.json")
OUTPUT_PATH = Path("data/json/legal_kg_demo_converted.json")


def classify_node(node):
    """Xác định loại node từ ID và dữ liệu nguồn."""

    node_id = node["id"]
    label = node.get("label", "")

    if node_id.startswith("vn:"):
        if ":chapter-" in node_id:
            return "Chapter"
        if ":article-" in node_id:
            if ":clause-" in node_id:
                if ":point-" in node_id:
                    return "Point"
                return "Clause"
            return "Article"
        return "Law"

    if node_id.startswith("concept:"):
        return "LegalConcept"

    if node_id.startswith("cond:"):
        return "LegalCondition"

    if node_id.startswith("subject:"):
        return "LegalSubject"

    if node_id.startswith("proc:"):
        return "LegalProcedure"

    raise ValueError(f"Không xác định được loại node: {node_id}")


def get_display_name(node):
    """Lấy tên hiển thị, không tự tạo nội dung pháp lý."""

    label = node.get("label", "")

    prefixes = [
        "LegalSubject: ",
        "LegalConcept: ",
        "LegalCondition: ",
        "LegalProcedure: ",
    ]

    for prefix in prefixes:
        if label.startswith(prefix):
            return label[len(prefix):]

    return label



def get_parent_info(node):
    """Xác định node cha dựa trên cấu trúc ID thực tế."""

    node_id = node["id"]

    # Điểm -> Khoản
    match = re.search(r":point-[a-z0-9]+$", node_id)
    if match:
        return (
            node_id[:match.start()],
            "points",
            "Clause"
        )

    # Khoản -> Điều
    match = re.search(r":clause-\d+$", node_id)
    if match:
        return (
            node_id[:match.start()],
            "clauses",
            "Article"
        )

    # Điều -> Luật hoặc Chương
    match = re.search(r":article-\d+$", node_id)
    if match:
        law_id = node_id.split(":article-")[0]

        return (
            law_id,
            "articles",
            "Law"
        )

    # Chương -> Luật
    match = re.search(r":chapter-\d+$", node_id)
    if match:
        return (
            node_id[:match.start()],
            "chapters",
            "Law"
        )

    return None


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file đầu vào: {INPUT_PATH}"
        )

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        source = json.load(f)

    source_nodes = source["nodes"]
    source_edges = source["edges"]

    # Kiểm tra ID trùng
    node_ids = [node["id"] for node in source_nodes]

    if len(node_ids) != len(set(node_ids)):
        raise ValueError("Phát hiện ID node bị trùng.")

    node_map = {}

    # Chuẩn hóa thuộc tính, giữ nguyên dữ liệu nguồn
    for original in source_nodes:
        node_type = classify_node(original)

        node = {
            "id": original["id"],
            "type": node_type,
            "name": get_display_name(original),
            "name_vi": get_display_name(original),
            "source_properties": original,
        }

        # Giữ label và title gốc nếu có
        if "label" in original:
            node["label"] = original["label"]

        if "title" in original:
            node["display_title"] = original["title"]

        node_map[node["id"]] = node

 
    # Phân chia node cấu trúc và node ngữ nghĩa
    documents = []
    semantic_nodes = []

    structural_types = {
        "Law", "Chapter", "Article", "Clause", "Point"
    }

    child_fields = {
        "Chapter": "chapters",
        "Article": "articles",
        "Clause": "clauses",
        "Point": "points",
    }

    # Khởi tạo các trường con cho node cấu trúc
    for node in node_map.values():
        if node["type"] in structural_types:
            for field in ["chapters", "articles", "clauses", "points"]:
                node[field] = []

            if node["type"] == "Law":
                documents.append(node)
        else:
            semantic_nodes.append(node)



    # Xây dựng cây phân cấp theo cạnh CONTAINS trong nguồn
    attached_nodes = set()

    for edge in source_edges:
        if edge["label"] != "CONTAINS":
            continue

        parent_id = edge["from"]
        child_id = edge["to"]

        if parent_id not in node_map:
            raise ValueError(f"Không tìm thấy node cha: {parent_id}")

        if child_id not in node_map:
            raise ValueError(f"Không tìm thấy node con: {child_id}")

        parent = node_map[parent_id]
        child = node_map[child_id]

        if parent["type"] not in structural_types:
            raise ValueError(
                f"Node cha không phải node cấu trúc: {parent_id}"
            )

        if child["type"] not in child_fields:
            raise ValueError(
                f"Node con không hợp lệ: {child_id}"
            )

        if child_id in attached_nodes:
            raise ValueError(
                f"Node có nhiều node cha CONTAINS: {child_id}"
            )

        child_field = child_fields[child["type"]]
        parent[child_field].append(child)
        attached_nodes.add(child_id)

    # Kiểm tra node cấu trúc chưa được gắn vào cây
    for node in node_map.values():
        if (
            node["type"] in structural_types
            and node["type"] != "Law"
            and node["id"] not in attached_nodes
        ):
            raise ValueError(
                f"Node cấu trúc chưa có quan hệ CONTAINS: {node['id']}"
            )

    # Chuyển đổi quan hệ, giữ nguyên loại quan hệ
    semantic_relationships = []

    valid_relations = {
        "CONTAINS",
        "REGULATES",
        "APPLIES_TO",
        "HAS_CONDITION",
        "HAS_PROCEDURE",
    }

    for edge in source_edges:
        if edge["from"] not in node_map:
            raise ValueError(f"Source không tồn tại: {edge['from']}")

        if edge["to"] not in node_map:
            raise ValueError(f"Target không tồn tại: {edge['to']}")

        relation = edge["label"]

        if relation not in valid_relations:
            raise ValueError(f"Quan hệ chưa được xác nhận: {relation}")

        semantic_relationships.append({
            "source": edge["from"],
            "target": edge["to"],
            "relation": relation,
            "source_properties": edge,
        })

    result = {
        "metadata": {
            "source": source.get("source"),
            "data_type": "demo",
            "description": (
                "KG demo được chuyển đổi từ dữ liệu vis-network. "
                "Không phải kho dữ liệu pháp luật đầy đủ."
            ),
        },
        "documents": documents,
        "semantic_nodes": semantic_nodes,
        "semantic_relationships": semantic_relationships,
    }

    # Kiểm tra node và quan hệ trước khi ghi file
    all_output_ids = set()

    def collect_ids(node):
        if node["id"] in all_output_ids:
            raise ValueError(f"ID xuất hiện nhiều lần: {node['id']}")

        all_output_ids.add(node["id"])

        for key in ["chapters", "articles", "clauses", "points"]:
            for child in node.get(key, []):
                collect_ids(child)

    for document in documents:
        collect_ids(document)

    for node in semantic_nodes:
        if node["id"] in all_output_ids:
            raise ValueError(f"ID trùng: {node['id']}")
        all_output_ids.add(node["id"])

    if len(all_output_ids) != len(source_nodes):
        raise ValueError("Số node sau chuyển đổi không khớp nguồn.")

    for rel in semantic_relationships:
        if rel["source"] not in all_output_ids:
            raise ValueError("Source của quan hệ không hợp lệ.")
        if rel["target"] not in all_output_ids:
            raise ValueError("Target của quan hệ không hợp lệ.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("CHUYEN DOI THANH CONG")
    print("Documents:", len(documents))
    print("Semantic nodes:", len(semantic_nodes))
    print("Relationships:", len(semantic_relationships))
    print("Total nodes:", len(all_output_ids))
    print("Output:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
