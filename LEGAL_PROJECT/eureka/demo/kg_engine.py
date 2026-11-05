
import json
import networkx as nx


class LegalKG:
    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.graph = nx.MultiDiGraph()
        self.nodes = {}

        # Nhận diện định dạng KG
        if "nodes" in self.data and "edges" in self.data:
            self._load_global_kg()
        else:
            self._load_demo_kg()

    # =====================================================
    # 1. LOAD KG DEMO CŨ
    # =====================================================

    def _load_demo_kg(self):
        for doc in self.data.get("documents", []):
            self._extract_node(doc)

        for node in self.data.get("semantic_nodes", []):
            self._extract_node(node)

        for rel in self.data.get("semantic_relationships", []):
            source = rel.get("source")
            target = rel.get("target")

            if source not in self.nodes or target not in self.nodes:
                continue

            self.graph.add_edge(
                source,
                target,
                **rel
            )

    def _extract_node(self, node):
        if not isinstance(node, dict):
            return

        node_id = node.get("id")

        if node_id:
            self.nodes[node_id] = node
            self.graph.add_node(node_id, **node)

        # Đệ quy các node cấu trúc lồng nhau
        for key in ["chapters", "sections", "articles", "clauses", "points"]:
            children = node.get(key, [])

            if isinstance(children, list):
                for child in children:
                    self._extract_node(child)

    # =====================================================
    # 2. LOAD GLOBAL KG
    # =====================================================

    def _load_global_kg(self):
        # Nạp toàn bộ node
        for node in self.data.get("nodes", []):
            if not isinstance(node, dict):
                continue

            node_id = node.get("id")

            if not node_id:
                continue

            self.nodes[node_id] = node
            self.graph.add_node(node_id, **node)

        # Nạp toàn bộ cạnh
        for edge in self.data.get("edges", []):
            if not isinstance(edge, dict):
                continue

            source = edge.get("source")
            target = edge.get("target")

            # Không tự tạo node ngầm nếu thiếu endpoint
            if source not in self.nodes or target not in self.nodes:
                continue

            # Giữ nguyên relation và inferred_relation
            # Không ghi đè quan hệ gốc UNKNOWN
            self.graph.add_edge(
                source,
                target,
                **edge
            )

    # =====================================================
    # 3. THỐNG KÊ KG
    # =====================================================

    def get_statistics(self):
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "node_types": self._count_node_types(),
            "relations": self._count_relations(),
        }

    def _count_node_types(self):
        counts = {}

        for node in self.nodes.values():
            node_type = node.get("type")

            if not node_type or node_type == "UNKNOWN":
                node_type = node.get("inferred_type", "UNKNOWN")

            counts[node_type] = counts.get(node_type, 0) + 1

        return counts

    def _count_relations(self):
        counts = {}

        for _, _, edge in self.graph.edges(data=True):
            relation = edge.get("relation")

            if not relation or relation == "UNKNOWN":
                relation = edge.get("inferred_relation")

            if not relation:
                relation = "UNKNOWN"

            counts[relation] = counts.get(relation, 0) + 1

        return counts