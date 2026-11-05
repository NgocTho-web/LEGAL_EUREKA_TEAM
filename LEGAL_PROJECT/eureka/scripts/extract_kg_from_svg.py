
import json
import xml.etree.ElementTree as ET
from pathlib import Path


# =====================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SVG_PATH = (
    PROJECT_ROOT
    / "data"
    / "visualization"
    / "global_legal_kg.svg"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "json"
    / "global_legal_kg_svg_extracted.json"
)

SVG_NAMESPACE = {
    "svg": "http://www.w3.org/2000/svg"
}


# =====================================================
# 2. ĐỌC NỘI DUNG SVG
# =====================================================

def load_svg(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file SVG: {path}"
        )

    tree = ET.parse(path)

    return tree.getroot()


# =====================================================
# 3. TRÍCH XUẤT NODES
# =====================================================

def extract_nodes(root):

    nodes = []

    elements = root.findall(
        './/svg:g[@class="node"]',
        SVG_NAMESPACE
    )

    for element in elements:

        title_element = element.find(
            "svg:title",
            SVG_NAMESPACE
        )

        if title_element is None:
            continue

        node_id = (
            title_element.text or ""
        ).strip()

        labels = []

        for text_element in element.findall(
            ".//svg:text",
            SVG_NAMESPACE
        ):

            label = "".join(
                text_element.itertext()
            ).strip()

            if label:
                labels.append(label)

        node_label = " ".join(labels)

        nodes.append({
            "id": node_id,
            "name": node_label,
            "type": "UNKNOWN",
            "source": "global_legal_kg.svg"
        })

    return nodes


# =====================================================
# 4. TRÍCH XUẤT EDGES
# =====================================================

def extract_edges(root):

    edges = []

    elements = root.findall(
        './/svg:g[@class="edge"]',
        SVG_NAMESPACE
    )

    for element in elements:

        title_element = element.find(
            "svg:title",
            SVG_NAMESPACE
        )

        if title_element is None:
            continue

        edge_title = (
            title_element.text or ""
        ).strip()

        if "->" not in edge_title:
            continue

        source, target = edge_title.split(
            "->",
            1
        )

        edges.append({
            "source": source.strip(),
            "target": target.strip(),
            "relation": "UNKNOWN",
            "source_file": "global_legal_kg.svg"
        })

    return edges


# =====================================================
# 5. KIỂM TRA CẤU TRÚC
# =====================================================

def validate_graph(nodes, edges):

    node_ids = {
        node["id"]
        for node in nodes
    }

    missing_endpoints = []

    for edge in edges:

        if edge["source"] not in node_ids:
            missing_endpoints.append(
                edge["source"]
            )

        if edge["target"] not in node_ids:
            missing_endpoints.append(
                edge["target"]
            )

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "unique_node_ids": len(node_ids),
        "duplicate_node_ids": (
            len(nodes) - len(node_ids)
        ),
        "edges_with_unknown_relation": len(
            edges
        ),
        "missing_endpoint_count": len(
            missing_endpoints
        ),
        "missing_endpoints": sorted(
            set(missing_endpoints)
        )
    }


# =====================================================
# 6. LƯU DỮ LIỆU
# =====================================================

def main():

    print("Đang đọc SVG...")

    root = load_svg(SVG_PATH)

    print("Đang trích xuất nodes...")

    nodes = extract_nodes(root)

    print("Đang trích xuất edges...")

    edges = extract_edges(root)

    validation = validate_graph(
        nodes,
        edges
    )

    result = {
        "metadata": {
            "name": "Global Legal Knowledge Graph",
            "source": "global_legal_kg.svg",
            "description": (
                "Dữ liệu cấu trúc trích xuất từ SVG. "
                "Các loại quan hệ chưa được xác minh "
                "được đánh dấu UNKNOWN."
            )
        },
        "nodes": nodes,
        "edges": edges,
        "validation": validation
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=4
        )

    print("\n========== KẾT QUẢ ==========")

    for key, value in validation.items():

        print(f"{key}: {value}")

    print("\nĐã lưu dữ liệu tại:")

    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
