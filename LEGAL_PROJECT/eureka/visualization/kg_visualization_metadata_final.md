# Metadata Thẩm Định Visualization (Bản Final)

## 1. Tổng Quan Chỉ Số Subgraph (Graph Metrics)

| Chỉ Số | Giá Trị | Ghi Chú Học Thuật |
|:---|:---:|:---|
| **Tổng số Nodes (Node Count)** | **13** | Nằm trong ngưỡng tối ưu [10–18 nodes] |
| **Tổng số Edges (Edge Count)** | **16** | Đảm bảo đồ thị liên thông hoàn toàn |
| **Số loại thực thể (Node Types)** | **6** | `Document`, `Component` (Article/Clause), `LegalConcept`, `LegalSubject`, `LegalCondition`, `LegalProcedure` |
| **Số loại quan hệ (Rel Types)** | **5** | `CONTAINS`, `REGULATES`, `APPLIES_TO`, `HAS_CONDITION`, `HAS_PROCEDURE` |

---

## 2. Chi Tiết Các Thực Thể (Node Types & Styling)

Màu sắc (Color Palette) cấu hình tuân thủ tuyệt đối bảng màu trong code. Kích thước (Radius) tùy chỉnh cố định để tối ưu hiển thị.

| STT | Node ID | Node Label | Entity Type | Color Code | Kích Thước |
|:---:|:---|:---|:---|:---:|:---:|
| 1 | `vn:law:2013...` | Luật Đất đai 2013 | `Document` | Muted Slate Navy (`#2B4C7E`) | Đồng đều |
| 2 | `...:article-188` | Điều 188 | `Component` | Academic Medium Blue (`#3182CE`) | Đồng đều |
| 3 | `...:clause-1` | Khoản 1 Điều 188 | `Component` | Steel Blue (`#4299E1`) | Đồng đều |
| 4 | `concept:quyen_su_dung_dat` | Quyền sử dụng đất | `LegalConcept` | Warm Terracotta (`#C05621`) | Đồng đều |
| 5 | `concept:chuyen_nhuong...` | Chuyển nhượng QSDĐ | `LegalConcept` | Warm Terracotta (`#C05621`) | Đồng đều |
| 6 | `concept:giay_chung_nhan...`| Giấy CN QSDĐ | `LegalConcept` | Warm Terracotta (`#C05621`) | Đồng đều |
| 7 | `subject:nguoi_su_dung_dat` | Người sử dụng đất | `LegalSubject` | Slate Charcoal (`#4A5568`) | Đồng đều |
| 8 | `cond:...` | 4 x Điều kiện pháp lý | `LegalCondition` | Forest Sage Green (`#2F855A`) | Đồng đều |
| 9 | `proc:...` | 2 x Thủ tục pháp lý | `LegalProcedure` | Scholarly Purple (`#6B46C1`) | Đồng đều |

*Ghi chú: Kích thước node được giữ đồng đều để làm nổi bật quan hệ ngữ nghĩa, theo thông lệ trực quan hoá Knowledge Graph học thuật.*

---

## 3. Đối chiếu 2 Pipeline Visualization

| Pipeline | Công cụ | File output | Trạng thái màu |
|:---|:---|:---|:---|
| Matplotlib (Gốc) | Python `render_bloom_view.py` | `visualization/matplotlib/legal_kg_matplotlib_final.png` | Đã đồng bộ (FILL gốc) |
| Neo4j Mock | Graphviz `create_bloom_mock.py` | `visualization/neo4j_bloom/neo4j_bloom_screenshot.png` | Đã đồng bộ (FILL gốc) |
