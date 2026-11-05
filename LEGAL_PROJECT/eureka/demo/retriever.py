
import unicodedata
import string
from collections import deque


class GraphRetriever:
    def __init__(self, kg):
        self.kg = kg
        self.graph = kg.graph
        self.nodes = kg.nodes

    # =========================================================
    # 1. CHUẨN HÓA TỪ KHÓA
    # =========================================================

    def _normalize(self, text):
        if not text:
            return ""

        text = str(text).lower()
        text = unicodedata.normalize("NFC", text)

        for char in string.punctuation:
            text = text.replace(char, " ")

        return " ".join(text.split())

    def _normalize_legal_term(self, text):
        text = str(text or "").lower().strip()

        replacements = {
            "qsdđ": "quyền sử dụng đất",
            "qsd": "quyền sử dụng đất",
            "gcn": "giấy chứng nhận",
        }

        for short, full in replacements.items():
            text = text.replace(short, full)

        return self._normalize(text)

    # =========================================================
    # 2. ĐỌC TYPE VÀ RELATION CHO HAI ĐỊNH DẠNG KG
    # =========================================================

    def _get_node_type(self, node):
        node_type = node.get("type")

        if not node_type or node_type == "UNKNOWN":
            node_type = node.get("inferred_type", "")

        return node_type or ""

 
    def _get_relation(self, edge_data):
        """
        Lấy quan hệ dùng cho truy vấn.
        Ưu tiên relation gốc; nếu UNKNOWN thì dùng inferred_relation.
        """
        relation = edge_data.get("relation")

        if not relation or relation == "UNKNOWN":
            relation = edge_data.get("inferred_relation", "")

        return relation or ""


    def _get_relation_status(self, edge_data):
        """
        Xác định trạng thái của quan hệ.

        Không mặc định quan hệ gốc là verified.
        """
        inference_status = edge_data.get("inference_status")
        verification_status = edge_data.get("verification_status")

        if verification_status == "verified":
            return "verified"

        if inference_status == "candidate":
            return "candidate"

        original_relation = edge_data.get("relation")

        if original_relation and original_relation != "UNKNOWN":
            return "unverified"

        return "unknown"

    def _get_node_name(self, node_id):
        node = self.nodes.get(node_id, {})

        return (
            node.get("name_vi")
            or node.get("name")
            or node.get("label")
            or node_id
        )

    def _is_structural_type(self, node_type):
        return node_type in {
            "Law",
            "Document",
            "Chapter",
            "Section",
            "Article",
            "Clause",
            "Point",
        }

    # =========================================================
    # 3. TÌM KIẾM THỰC THỂ PHÁP LÝ
    # =========================================================

    def search_legal_entity(self, query):
        results = []

        norm_query = self._normalize_legal_term(query)

        if not norm_query:
            return results

        allowed_types = {
            "LegalAction",
            "LegalConcept",
            "LegalProcedure",
            "LegalCondition",
            "LegalSubject",
        }

        query_tokens = set(norm_query.split())

        for node_id, node in self.nodes.items():
            node_type = self._get_node_type(node)

            if node_type not in allowed_types:
                continue

            name_vi = node.get("name_vi", "")
            name = node.get("name", "")

            norm_name_vi = self._normalize_legal_term(name_vi)
            norm_name = self._normalize_legal_term(name)

            candidate = norm_name_vi or norm_name

            if not candidate:
                continue

            name_tokens = set(candidate.split())
            common_tokens = query_tokens & name_tokens

            if not common_tokens:
                continue

            coverage = len(common_tokens) / len(query_tokens)
            precision = len(common_tokens) / len(name_tokens)

            if candidate == norm_query:
                score = 1.0

            elif candidate in norm_query:
                score = 0.85 + 0.15 * coverage

            elif norm_query in candidate:
                score = 0.80 + 0.20 * precision

            else:
                score = 0.70 * coverage + 0.30 * precision

            if score >= 0.45:
                results.append({
                    "id": node_id,
                    "name_vi": name_vi or name,
                    "type": node_type,
                    "score": round(score, 4),
                })

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results

    # =========================================================
    # 4. TÌM NODE CẤU TRÚC LIÊN KẾT VỚI KHÁI NIỆM
    # =========================================================


    def _get_structural_sources(self, target_id):
        """
        Lấy node cấu trúc có quan hệ REGULATES.

        Cho phép lấy cả quan hệ suy luận để phục vụ truy xuất.
        Trạng thái quan hệ phải được giữ lại để phân biệt
        candidate và unverified với verified.
        """
        structural_sources = set()

        if target_id not in self.graph:
            return structural_sources

        for source_id, _, edge_data in self.graph.in_edges(
            target_id, data=True
        ):
            relation = self._get_relation(edge_data)

            if relation != "REGULATES":
                continue

            source_node = self.nodes.get(source_id, {})
            source_type = self._get_node_type(source_node)

            if self._is_structural_type(source_type):
                structural_sources.add(source_id)

        return structural_sources


    # =========================================================
    # 5. TRUY NGƯỢC CẤU TRÚC PHÁP LÝ
    # =========================================================

    def _get_structural_paths(self, start_ids):
        """
        Truy ngược từ node cấu trúc lên node cha
        thông qua cạnh CONTAINS.

        Ví dụ:
        Khoản 1 -> Điều 188

        Kết quả:
        [Điều 188, Khoản 1]

        Chỉ sử dụng quan hệ CONTAINS.
        Không tự chuyển UNKNOWN thành CONTAINS.
        """

        results = []

        for start_id in start_ids:
            if start_id not in self.graph:
                continue

            queue = deque([(start_id, [start_id])])

            while queue:
                current_id, path = queue.popleft()

                parents = []

                for parent_id, _, edge_data in self.graph.in_edges(
                    current_id, data=True
                ):
                    if self._get_relation(edge_data) == "CONTAINS":
                        parents.append(parent_id)

                # Không còn node cha: hoàn thành một đường dẫn
                if not parents:
                    results.append(list(reversed(path)))
                    continue

                for parent_id in parents:
                    if parent_id not in path:
                        queue.append(
                            (parent_id, path + [parent_id])
                        )

        # Loại bỏ các đường dẫn trùng nhau
        unique_paths = []
        seen = set()

        for path in results:
            key = tuple(path)

            if key not in seen:
                seen.add(key)
                unique_paths.append(path)

        return unique_paths

    # =========================================================
    # 6. TẠO NỘI DUNG CẤU TRÚC CÓ NGỮ CẢNH
    # =========================================================


    def _build_structural_contents(self, structural_paths):
        """
        Xây dựng nội dung cấu trúc pháp luật.

        Giữ lại:
        - ID node
        - Tên và loại node
        - Đường dẫn phân cấp
        - Tiêu đề và nội dung
        - Metadata nguồn
        """

        structural_contents = []

        type_order = {
            "Law": 1,
            "Document": 1,
            "Chapter": 2,
            "Section": 3,
            "Article": 4,
            "Clause": 5,
            "Point": 6,
        }

        seen_sources = set()

        for path in structural_paths:

            if not path:
                continue

            hierarchy = []
            hierarchy_text = []

            for node_id in path:

                node = self.nodes.get(node_id, {})

                name = self._get_node_name(node_id)
                node_type = self._get_node_type(node)

                title = (
                    node.get("display_title")
                    or node.get("title")
                    or ""
                )

                content = (
                    node.get("content")
                    or node.get("content_text")
                    or ""
                )

                hierarchy.append({
                    "id": node_id,
                    "name": name,
                    "type": node_type,
                    "title": title,
                    "content": content,
                })

                hierarchy_text.append(name)

            source_id = path[-1]

            # Tránh tạo nội dung cấu trúc trùng node nguồn.
            if source_id in seen_sources:
                continue

            seen_sources.add(source_id)

            source_node = self.nodes.get(source_id, {})

            source_title = (
                source_node.get("display_title")
                or source_node.get("title")
                or ""
            )

            source_content = (
                source_node.get("content")
                or source_node.get("content_text")
                or ""
            )

            structural_contents.append({
                "id": source_id,
                "name": self._get_node_name(source_id),
                "type": self._get_node_type(source_node),
                "hierarchy": hierarchy,
                "hierarchy_text": " > ".join(hierarchy_text),
                "title": source_title,
                "content": source_content,
                "text": "\n".join(
                    part for part in [
                        " > ".join(hierarchy_text),
                        source_title,
                        source_content,
                    ]
                    if part
                ),
                "source_properties": source_node.get(
                    "source_properties", {}
                ),
                "verification_status": "Unverified",
            })

        structural_contents.sort(
            key=lambda item: (
                type_order.get(item["type"], 99),
                item["hierarchy_text"],
                item["id"],
            )
        )

        return structural_contents


    # =========================================================
    # 7. TRUY XUẤT ĐƯỜNG DẪN SUY LUẬN
    # =========================================================

    def get_reasoning_path(self, target_node_id):
        """
        Truy xuất đường dẫn suy luận từ một thực thể.

        Phân biệt:
        - Inferred: quan hệ được suy luận, trạng thái candidate.
        - Unverified: chưa đủ dữ liệu xác minh.
        
        Không tự động đánh dấu quan hệ là Verified.
        """

        if target_node_id not in self.nodes:
            return [], [], []

        paths = []
        evidence_list = []

        target_node = self.nodes[target_node_id]
        target_type = self._get_node_type(target_node)
        target_name = self._get_node_name(target_node_id)

        reasoning_sources = [target_node_id]

        # -----------------------------------------------------
        # Hàm tạo evidence thống nhất
        # -----------------------------------------------------

        def make_evidence(source_id, child_id, edge_data, relation):
            return {
                "relation": relation,
                "source_node_id": source_id,
                "target_node_id": child_id,
                "target_node": self.nodes.get(child_id, {}),
                "original_relation": edge_data.get("relation"),
                "inferred_relation": edge_data.get("inferred_relation"),
                "inference_basis": edge_data.get("inference_basis"),
                "evidence_text": edge_data.get("evidence"),
                "source_reference": edge_data.get("source_reference"),
                "inference_status": edge_data.get(
                    "inference_status", "unknown"
                ),
                "verification_status": self._get_relation_status(
                    edge_data
                ),
            }

        # -----------------------------------------------------
        # 1. Tìm khái niệm liên quan nếu node chính là thủ tục
        # -----------------------------------------------------

        if target_type == "LegalProcedure":

            for source_id, _, edge_data in self.graph.in_edges(
                target_node_id, data=True
            ):
                relation = self._get_relation(edge_data)

                if relation != "HAS_PROCEDURE":
                    continue

                if source_id not in reasoning_sources:
                    reasoning_sources.append(source_id)

                source_name = self._get_node_name(source_id)

                paths.append(
                    f"[{source_name}] --HAS_PROCEDURE--> "
                    f"[{target_name}]"
                )

                evidence_list.append(
                    make_evidence(
                        source_id,
                        target_node_id,
                        edge_data,
                        relation,
                    )
                )

        # -----------------------------------------------------
        # 2. Truy xuất điều kiện, thủ tục, đối tượng áp dụng
        # -----------------------------------------------------

        allowed_relations = {
            "HAS_CONDITION",
            "HAS_PROCEDURE",
            "APPLIES_TO",
        }

        for reasoning_id in reasoning_sources:

            reasoning_name = self._get_node_name(reasoning_id)

            for _, child_id, edge_data in self.graph.out_edges(
                reasoning_id, data=True
            ):
                relation = self._get_relation(edge_data)

                if relation not in allowed_relations:
                    continue

                if (
                    target_type == "LegalProcedure"
                    and child_id == target_node_id
                ):
                    continue

                child_name = self._get_node_name(child_id)

                paths.append(
                    f"[{reasoning_name}] --{relation}--> "
                    f"[{child_name}]"
                )

                evidence_list.append(
                    make_evidence(
                        reasoning_id,
                        child_id,
                        edge_data,
                        relation,
                    )
                )

        # -----------------------------------------------------
        # 3. Phân loại nguồn cấu trúc
        # -----------------------------------------------------

        verified_sources = set()
        candidate_sources = set()

        for reasoning_id in reasoning_sources:

            if reasoning_id not in self.graph:
                continue

            for source_id, _, edge_data in self.graph.in_edges(
                reasoning_id, data=True
            ):
                relation = self._get_relation(edge_data)

                if relation != "REGULATES":
                    continue

                source_node = self.nodes.get(source_id, {})
                source_type = self._get_node_type(source_node)

                if not self._is_structural_type(source_type):
                    continue

                status = self._get_relation_status(edge_data)

                if status == "Inferred":
                    candidate_sources.add(source_id)
                else:
                    # Chưa đủ bằng chứng để gọi là Verified.
                    verified_sources.add(source_id)

                paths.append(
                    f"[{self._get_node_name(source_id)}] "
                    f"--REGULATES--> "
                    f"[{self._get_node_name(reasoning_id)}]"
                )

                evidence_list.append(
                    make_evidence(
                        source_id,
                        reasoning_id,
                        edge_data,
                        relation,
                    )
                )

        # -----------------------------------------------------
        # 4. Truy xuất cây cấu trúc
        # -----------------------------------------------------

        all_structural_sources = (
            verified_sources | candidate_sources
        )

        structural_paths = self._get_structural_paths(
            all_structural_sources
        )

        structural_contents = self._build_structural_contents(
            structural_paths
        )

        # Gắn trạng thái cho từng nội dung cấu trúc.
        for item in structural_contents:

            if item["id"] in candidate_sources:
                item["verification_status"] = "Inferred"

            elif item["id"] in verified_sources:
                item["verification_status"] = "Unverified"

            else:
                item["verification_status"] = "Unverified"

        # -----------------------------------------------------
        # 5. Loại bỏ evidence trùng lặp
        # -----------------------------------------------------

        unique_evidence = {}

        for item in evidence_list:

            key = (
                item["relation"],
                item["source_node_id"],
                item["target_node_id"],
            )

            if key not in unique_evidence:
                unique_evidence[key] = item

        paths = list(dict.fromkeys(paths))

        return (
            paths,
            list(unique_evidence.values()),
            structural_contents,
        )
