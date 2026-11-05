
import json
from pathlib import Path
from collections import defaultdict
from typing import Any
import re


class LegalKGEngine:
    """
    KG Engine đọc và truy xuất Knowledge Graph Stage 3.

    Lưu ý:
    - Giữ nguyên type và relation gốc.
    - inferred_type và inferred_relation chỉ là kết quả suy luận.
    - Không xem các quan hệ candidate là quan hệ pháp lý đã xác minh.
    - KG hiện tại không chứa nội dung chi tiết của điều luật.
    """

    def __init__(self, kg_path: str | Path | None = None):
        project_root = Path(__file__).resolve().parents[2]

        self.kg_path = (
            Path(kg_path)
            if kg_path
            else project_root
            / "data"
            / "json"
            / "global_legal_kg_stage3.json"
        )

        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []

        self.node_by_id: dict[str, dict[str, Any]] = {}
        self.outgoing = defaultdict(list)
        self.incoming = defaultdict(list)

        self._load()

    def _load(self):
        if not self.kg_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy KG: {self.kg_path}"
            )

        with self.kg_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("KG phải có cấu trúc root là dict.")

        self.nodes = data.get("nodes", [])
        self.edges = data.get("edges", [])

        if not isinstance(self.nodes, list):
            raise ValueError("Trường nodes không phải list.")

        if not isinstance(self.edges, list):
            raise ValueError("Trường edges không phải list.")

        self.node_by_id = {
            node["id"]: node
            for node in self.nodes
            if isinstance(node, dict) and node.get("id")
        }

        child_edges = [
            edge
            for edge in self.outgoing[parent_id]
            if edge.get("inferred_relation") == "CONTAINS"
        ]

        child_edges.sort(
            key=lambda edge: self._natural_sort_key(
                self.node_by_id[edge["target"]]
            )
        )

        for edge in child_edges:

            source = edge.get("source")
            target = edge.get("target")

            if source not in self.node_by_id:
                continue

            if target not in self.node_by_id:
                continue

            self.outgoing[source].append(edge)
            self.incoming[target].append(edge)

    def get_statistics(self):
        """Trả về thống kê cơ bản của KG."""

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "indexed_nodes": len(self.node_by_id),
            "total_outgoing_links": sum(
                len(items) for items in self.outgoing.values()
            ),
            "total_incoming_links": sum(
                len(items) for items in self.incoming.values()
            ),
        }

    def get_node(self, node_id: str):
        """Tìm node bằng ID."""

        return self.node_by_id.get(node_id)

    def search_nodes(
        self,
        keyword: str,
        inferred_type: str | None = None,
        limit: int = 20
    ):
        """
        Tìm node theo tên hoặc ID.

        inferred_type là bộ lọc theo loại suy luận,
        không phải type gốc đã xác minh.
        """

        keyword = keyword.strip().casefold()

        if not keyword:
            return []

        results = []

        for node in self.nodes:
            name = str(node.get("name", ""))
            node_id = str(node.get("id", ""))

            matched = (
                keyword in name.casefold()
                or keyword in node_id.casefold()
            )

            if not matched:
                continue

            if inferred_type:
                if node.get("inferred_type") != inferred_type:
                    continue

            results.append(node)

            if len(results) >= limit:
                break

        return results

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
        include_candidate: bool = True
    ):
        """
        Lấy node liên kết với node được chỉ định.

        direction:
        - outgoing: các node đích
        - incoming: các node nguồn
        - both: cả hai chiều

        Mặc định bao gồm cả quan hệ candidate.
        """

        if node_id not in self.node_by_id:
            return []

        if direction not in {"outgoing", "incoming", "both"}:
            raise ValueError(
                "direction phải là outgoing, incoming hoặc both."
            )

        edges = []

        if direction in {"outgoing", "both"}:
            edges.extend(self.outgoing[node_id])

        if direction in {"incoming", "both"}:
            edges.extend(self.incoming[node_id])

        results = []

        for edge in edges:
            status = edge.get("inference_status")

            if not include_candidate and status == "candidate":
                continue

            if edge.get("source") == node_id:
                neighbor_id = edge.get("target")
                direction_label = "outgoing"
            else:
                neighbor_id = edge.get("source")
                direction_label = "incoming"

            neighbor = self.node_by_id.get(neighbor_id)

            if neighbor:
                results.append({
                    "node": neighbor,
                    "direction": direction_label,
                    "original_relation": edge.get("relation"),
                    "inferred_relation": edge.get(
                        "inferred_relation"
                    ),
                    "inference_status": status,
                    "inference_basis": edge.get("inference_basis"),
                    "source_file": edge.get("source_file"),
                })

        return results

    def get_document_structure(self, document_id: str):
        """
        Truy xuất cấu trúc phân cấp của một văn bản.

        Chỉ sử dụng các cạnh inferred_relation = CONTAINS.
        Kết quả vẫn được đánh dấu là quan hệ suy luận.
        """

        document = self.get_node(document_id)

        if not document:
            return None

        visited = set()
        structure = []

        def traverse(parent_id, depth):
            if parent_id in visited:
                return

            visited.add(parent_id)

            for edge in self.outgoing[parent_id]:
                if edge.get("inferred_relation") != "CONTAINS":
                    continue

                child_id = edge.get("target")
                child = self.node_by_id.get(child_id)

                if not child:
                    continue

                structure.append({
                    "depth": depth,
                    "id": child.get("id"),
                    "name": child.get("name"),
                    "inferred_type": child.get("inferred_type"),
                    "original_type": child.get("type"),
                    "relation_status": edge.get(
                        "inference_status"
                    ),
                    "inference_basis": edge.get(
                        "inference_basis"
                    ),
                })

                traverse(child_id, depth + 1)

        traverse(document_id, 1)

        return {
            "document": document,
            "structure": structure,
            "structure_is_verified": False,
        }
    @staticmethod
    def _natural_sort_key(node):
        """
        Sắp xếp tên node theo số tự nhiên.
        Ví dụ: Chương 1, Chương 2, Chương 10.
        """
        name = str(node.get("name", ""))

        parts = re.split(r"(\d+)", name)

        return [
            int(part) if part.isdigit() else part.casefold()
            for part in parts
        ]